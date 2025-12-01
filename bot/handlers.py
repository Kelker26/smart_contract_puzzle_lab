import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from bot.admin import cmd_admin_stats, cmd_dump, cmd_user


from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from bot.db_storage import (  # Changed from bot.storage
    set_username,
    get_username,
    mark_puzzle_solved,
    record_wrong_answer,
    get_last_wrong,
    get_user_progress,
    get_leaderboard,
    get_user_stage,
    advance_user_stage,
    get_random_unsolved_puzzle,
    is_puzzle_solved,
    record_award,
    get_user_awards,
    get_perfect_solve_count,
    is_award_earned,
    add_bonus_points,
    get_session_stats,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Temporary in-memory set for users who must provide username
USER_NAME_PENDING = set()

# Enhanced puzzle bank with multiple puzzles per difficulty
PUZZLES = {
    # ==================== BEGINNER ====================
    "beginner_1": {
        "question": (
            "🧩 *Puzzle B1 — Simple Storage*\n\n"
            "```solidity\n"
            "pragma solidity ^0.8.0;\n\n"
            "contract SimpleStorage {\n"
            "    uint public value = 42;\n"
            "}\n"
            "```\n"
            "❓ *Question:* What number will `value` return?"
        ),
        "answer": "42",
        "explanation": "The `value` variable is initialized to 42 in the contract. Public variables automatically get a getter function.",
        "difficulty": "Beginner",
        "points": 10,
        "stage_required": 1,
    },
    "beginner_2": {
        "question": (
            "🧩 *Puzzle B2 — Basic Addition*\n\n"
            "```solidity\n"
            "contract Math {\n"
            "    function add(uint a, uint b) public pure returns (uint) {\n"
            "        return a + b;\n"
            "    }\n"
            "}\n"
            "```\n"
            "❓ *Question:* What does `add(5, 10)` return?"
        ),
        "answer": "15",
        "explanation": "Simple addition: 5 + 10 = 15. The function is marked `pure` because it doesn't read or modify state.",
        "difficulty": "Beginner",
        "points": 10,
        "stage_required": 1,
    },
    "beginner_3": {
        "question": (
            "🧩 *Puzzle B3 — Boolean Logic*\n\n"
            "```solidity\n"
            "contract Logic {\n"
            "    bool public isActive = true;\n"
            "    \n"
            "    function toggle() public {\n"
            "        isActive = !isActive;\n"
            "    }\n"
            "}\n"
            "```\n"
            "❓ *Question:* What is `isActive` after calling `toggle()` once? (answer: true or false)"
        ),
        "answer": "false",
        "explanation": "The `!` operator inverts the boolean. Since `isActive` starts as true, `!true` equals false.",
        "difficulty": "Beginner",
        "points": 10,
        "stage_required": 1,
    },
    "beginner_4": {
        "question": (
            "🧩 *Puzzle B4 — String Basics*\n\n"
            "```solidity\n"
            "contract Greeter {\n"
            "    string public greeting = \"Hello\";\n"
            "}\n"
            "```\n"
            "❓ *Question:* What does the `greeting` variable store? (one word)"
        ),
        "answer": "hello",
        "explanation": "The string is initialized with \"Hello\". String variables in Solidity store text data.",
        "difficulty": "Beginner",
        "points": 10,
        "stage_required": 1,
    },
    
    # ==================== INTERMEDIATE ====================
    "intermediate_1": {
        "question": (
            "🧩 *Puzzle I1 — Mapping Basics*\n\n"
            "```solidity\n"
            "contract Balances {\n"
            "    mapping(address => uint) public balances;\n\n"
            "    constructor() {\n"
            "        balances[msg.sender] = 100;\n"
            "    }\n"
            "}\n"
            "```\n"
            "❓ *Question:* What will `balances[msg.sender]` return for the deployer?"
        ),
        "answer": "100",
        "explanation": "The constructor sets the deployer's balance to 100. `msg.sender` in the constructor is the deploying address.",
        "difficulty": "Intermediate",
        "points": 20,
        "stage_required": 2,
    },
    "intermediate_2": {
        "question": (
            "🧩 *Puzzle I2 — Counter & Events*\n\n"
            "```solidity\n"
            "contract Counter {\n"
            "    uint public count;\n\n"
            "    event Incremented(uint newValue);\n\n"
            "    function increment() public {\n"
            "        count += 1;\n"
            "        emit Incremented(count);\n"
            "    }\n"
            "}\n"
            "```\n"
            "❓ *Question:* What is `count` after calling `increment()` twice?"
        ),
        "answer": "2",
        "explanation": "Starting from 0, each call adds 1. After two calls: 0 → 1 → 2. Events log the changes but don't affect the state.",
        "difficulty": "Intermediate",
        "points": 20,
        "stage_required": 2,
    },
    "intermediate_3": {
        "question": (
            "🧩 *Puzzle I3 — The Private Illusion*\n\n"
            "```solidity\n"
            "contract Vault {\n"
            "    bytes32 private password;\n"
            "    \n"
            "    constructor(bytes32 _password) {\n"
            "        password = _password;\n"
            "    }\n"
            "}\n"
            "```\n"
            "❓ *Question:* Can someone read the `password` value from the blockchain? (yes/no)"
        ),
        "answer": "yes",
        "explanation": "🚨 Common vulnerability! The `private` keyword only prevents other CONTRACTS from accessing the data. Anyone can read storage slots directly from the blockchain. Never store sensitive data in 'private' variables!",
        "difficulty": "Intermediate",
        "points": 20,
        "stage_required": 2,
    },
    "intermediate_4": {
        "question": (
            "🧩 *Puzzle I4 — Modifier Logic*\n\n"
            "```solidity\n"
            "contract Owned {\n"
            "    address public owner;\n"
            "    \n"
            "    constructor() {\n"
            "        owner = msg.sender;\n"
            "    }\n"
            "    \n"
            "    modifier onlyOwner() {\n"
            "        require(msg.sender == owner);\n"
            "        _;\n"
            "    }\n"
            "}\n"
            "```\n"
            "❓ *Question:* Can someone other than the owner call a function with the `onlyOwner` modifier? (yes/no)"
        ),
        "answer": "no",
        "explanation": "The `onlyOwner` modifier checks if `msg.sender == owner`. If not, the `require` statement fails and reverts the transaction.",
        "difficulty": "Intermediate",
        "points": 20,
        "stage_required": 2,
    },
    
    # ==================== ADVANCED ====================
    "advanced_1": {
        "question": (
            "🧩 *Puzzle A1 — Reentrancy Vulnerability*\n\n"
            "```solidity\n"
            "contract Bank {\n"
            "    mapping(address => uint) public balances;\n"
            "    \n"
            "    function withdraw(uint amount) public {\n"
            "        require(balances[msg.sender] >= amount);\n"
            "        payable(msg.sender).transfer(amount);\n"
            "        balances[msg.sender] -= amount;\n"
            "    }\n"
            "}\n"
            "```\n"
            "❓ *Question:* What's the primary vulnerability? (one word)"
        ),
        "answer": "reentrancy",
        "explanation": "🚨 Classic reentrancy attack! Balance is updated AFTER the transfer. An attacker can call withdraw() again before the balance updates. Fix: Update state before external calls (Checks-Effects-Interactions pattern) or use ReentrancyGuard.",
        "difficulty": "Advanced",
        "points": 30,
        "stage_required": 3,
    },
    "advanced_2": {
        "question": (
            "🧩 *Puzzle A2 — Delegatecall Danger*\n\n"
            "```solidity\n"
            "contract Proxy {\n"
            "    address public owner;\n"
            "    address public lib;\n"
            "    \n"
            "    function execute(bytes memory data) public {\n"
            "        lib.delegatecall(data);\n"
            "    }\n"
            "}\n"
            "```\n"
            "❓ *Question:* Can delegatecall modify the Proxy's storage? (yes/no)"
        ),
        "answer": "yes",
        "explanation": "🚨 Delegatecall executes code in the context of the CALLING contract! It can modify storage slots. If the library has a function that changes 'owner', it will change the Proxy's owner. Always be careful with delegatecall and untrusted libraries.",
        "difficulty": "Advanced",
        "points": 30,
        "stage_required": 3,
    },
    "advanced_3": {
        "question": (
            "🧩 *Puzzle A3 — Integer Overflow (Pre-0.8.0)*\n\n"
            "```solidity\n"
            "// Solidity 0.7.x\n"
            "contract Old {\n"
            "    uint8 public value = 255;\n"
            "    \n"
            "    function increment() public {\n"
            "        value = value + 1;\n"
            "    }\n"
            "}\n"
            "```\n"
            "❓ *Question:* In Solidity 0.7.x, what is `value` after calling `increment()`?"
        ),
        "answer": "0",
        "explanation": "🚨 In Solidity versions before 0.8.0, integers could overflow! uint8 max is 255. Adding 1 wraps around to 0. Solidity 0.8.0+ has built-in overflow protection, but older contracts are vulnerable. Always use SafeMath in older versions!",
        "difficulty": "Advanced",
        "points": 30,
        "stage_required": 3,
    },
    "advanced_4": {
        "question": (
            "🧩 *Puzzle A4 — tx.origin vs msg.sender*\n\n"
            "```solidity\n"
            "contract Auth {\n"
            "    address public owner;\n"
            "    \n"
            "    constructor() { owner = msg.sender; }\n"
            "    \n"
            "    function transfer(address newOwner) public {\n"
            "        require(tx.origin == owner);\n"
            "        owner = newOwner;\n"
            "    }\n"
            "}\n"
            "```\n"
            "❓ *Question:* Is using tx.origin for authentication safe? (yes/no)"
        ),
        "answer": "no",
        "explanation": "🚨 Never use tx.origin for auth! tx.origin is the ORIGINAL sender of the transaction. If the owner calls a malicious contract, that contract can call transfer() and tx.origin will still be the owner. Always use msg.sender for authentication!",
        "difficulty": "Advanced",
        "points": 30,
        "stage_required": 3,
    },
    "advanced_5": {
        "question": (
            "🧩 *Puzzle A5 — Unchecked External Call*\n\n"
            "```solidity\n"
            "contract Sender {\n"
            "    function send(address payable recipient) public payable {\n"
            "        recipient.send(msg.value);\n"
            "    }\n"
            "}\n"
            "```\n"
            "❓ *Question:* What happens if send() fails? Will the transaction revert? (yes/no)"
        ),
        "answer": "no",
        "explanation": "🚨 The send() function returns a boolean but doesn't revert on failure! If the recipient rejects the payment, send() returns false but execution continues. Always check the return value or use transfer() which reverts on failure. Better yet, use the withdrawal pattern!",
        "difficulty": "Advanced",
        "points": 30,
        "stage_required": 3,
    },
    
    # ==================== MORE BEGINNER PUZZLES ====================
    "beginner_5": {
        "question": (
            "🧩 *Puzzle B5 — Array Length*\n\n"
            "```solidity\n"
            "contract Arrays {\n"
            "    uint[] public numbers = [1, 2, 3, 4, 5];\n"
            "    \n"
            "    function getLength() public view returns (uint) {\n"
            "        return numbers.length;\n"
            "    }\n"
            "}\n"
            "```\n"
            "❓ *Question:* What does getLength() return?"
        ),
        "answer": "5",
        "explanation": "Arrays have a .length property that returns the number of elements. This array has 5 elements (1,2,3,4,5).",
        "difficulty": "Beginner",
        "points": 10,
        "stage_required": 1,
    },
    "beginner_6": {
        "question": (
            "🧩 *Puzzle B6 — Payable Functions*\n\n"
            "```solidity\n"
            "contract Payment {\n"
            "    function deposit() public payable {\n"
            "        // Accept ETH\n"
            "    }\n"
            "}\n"
            "```\n"
            "❓ *Question:* Can this function receive ETH? (yes/no)"
        ),
        "answer": "yes",
        "explanation": "The 'payable' modifier allows a function to receive ETH. Without it, transactions sending ETH would revert.",
        "difficulty": "Beginner",
        "points": 10,
        "stage_required": 1,
    },
    "beginner_7": {
        "question": (
            "🧩 *Puzzle B7 — View vs Pure*\n\n"
            "```solidity\n"
            "contract Functions {\n"
            "    uint public x = 10;\n"
            "    \n"
            "    function getX() public view returns (uint) {\n"
            "        return x;\n"
            "    }\n"
            "}\n"
            "```\n"
            "❓ *Question:* Does 'view' mean it reads state? (yes/no)"
        ),
        "answer": "yes",
        "explanation": "'view' functions can READ state but can't modify it. 'pure' functions can't even read state. This function reads 'x' so it must be 'view'.",
        "difficulty": "Beginner",
        "points": 10,
        "stage_required": 1,
    },
    
    # ==================== MORE INTERMEDIATE PUZZLES ====================
    "intermediate_5": {
        "question": (
            "🧩 *Puzzle I5 — Gas Optimization*\n\n"
            "```solidity\n"
            "contract Storage {\n"
            "    uint256 public a;\n"
            "    uint256 public b;\n"
            "    \n"
            "    function updateBoth(uint256 _a, uint256 _b) public {\n"
            "        a = _a;\n"
            "        b = _b;\n"
            "    }\n"
            "}\n"
            "```\n"
            "❓ *Question:* Which is cheaper: reading from storage or memory? (storage/memory)"
        ),
        "answer": "memory",
        "explanation": "⚡ Memory is MUCH cheaper than storage! Reading storage costs 100+ gas, memory costs 3 gas. Always cache storage variables in memory if used multiple times. Storage writes are the most expensive (20,000+ gas for new slots)!",
        "difficulty": "Intermediate",
        "points": 20,
        "stage_required": 2,
    },
    "intermediate_6": {
        "question": (
            "🧩 *Puzzle I6 — Timestamp Dependency*\n\n"
            "```solidity\n"
            "contract Lottery {\n"
            "    function random() public view returns (uint) {\n"
            "        return uint(keccak256(abi.encodePacked(block.timestamp)));\n"
            "    }\n"
            "}\n"
            "```\n"
            "❓ *Question:* Is block.timestamp safe for randomness? (yes/no)"
        ),
        "answer": "no",
        "explanation": "🚨 Never use block.timestamp, block.number, or blockhash for randomness! Miners can manipulate these values within limits. Use Chainlink VRF or commit-reveal schemes for true randomness.",
        "difficulty": "Intermediate",
        "points": 20,
        "stage_required": 2,
    },
    "intermediate_7": {
        "question": (
            "🧩 *Puzzle I7 — ERC20 Approval*\n\n"
            "```solidity\n"
            "// Simplified ERC20\n"
            "contract Token {\n"
            "    mapping(address => mapping(address => uint)) public allowance;\n"
            "    \n"
            "    function approve(address spender, uint amount) public {\n"
            "        allowance[msg.sender][spender] = amount;\n"
            "    }\n"
            "}\n"
            "```\n"
            "❓ *Question:* After approve(), can the spender transfer YOUR tokens? (yes/no)"
        ),
        "answer": "yes",
        "explanation": "ERC20 approval gives another address permission to spend your tokens. They can call transferFrom() to move tokens from your balance. Always be careful what contracts you approve!",
        "difficulty": "Intermediate",
        "points": 20,
        "stage_required": 2,
    },
    "intermediate_8": {
        "question": (
            "🧩 *Puzzle I8 — Front-Running*\n\n"
            "```solidity\n"
            "contract Auction {\n"
            "    uint public highestBid;\n"
            "    \n"
            "    function bid() public payable {\n"
            "        require(msg.value > highestBid);\n"
            "        highestBid = msg.value;\n"
            "    }\n"
            "}\n"
            "```\n"
            "❓ *Question:* Can miners see your transaction before confirming it? (yes/no)"
        ),
        "answer": "yes",
        "explanation": "🚨 Front-running attack! Transactions sit in the mempool before being mined. Anyone (especially miners) can see pending transactions and submit their own with higher gas to get confirmed first. Use commit-reveal or private mempools to prevent this!",
        "difficulty": "Intermediate",
        "points": 20,
        "stage_required": 2,
    },
    
    # ==================== MORE ADVANCED PUZZLES ====================
    "advanced_6": {
        "question": (
            "🧩 *Puzzle A6 — Selfdestruct Vulnerability*\n\n"
            "```solidity\n"
            "contract Wallet {\n"
            "    function getBalance() public view returns (uint) {\n"
            "        return address(this).balance;\n"
            "    }\n"
            "}\n"
            "```\n"
            "❓ *Question:* Can someone force ETH into this contract without calling a function? (yes/no)"
        ),
        "answer": "yes",
        "explanation": "🚨 Selfdestruct force-send attack! Any contract can selfdestruct and force-send ETH to any address, bypassing all checks. Never rely on address(this).balance for logic - an attacker can manipulate it!",
        "difficulty": "Advanced",
        "points": 30,
        "stage_required": 3,
    },
    "advanced_7": {
        "question": (
            "🧩 *Puzzle A7 — Flash Loan Attack*\n\n"
            "```solidity\n"
            "contract SimpleDEX {\n"
            "    function price() public view returns (uint) {\n"
            "        return token1.balanceOf(address(this)) / token2.balanceOf(address(this));\n"
            "    }\n"
            "}\n"
            "```\n"
            "❓ *Question:* Can price be manipulated within a single transaction? (yes/no)"
        ),
        "answer": "yes",
        "explanation": "🚨 Classic flash loan/price manipulation! An attacker can borrow massive amounts, manipulate the pool ratio, exploit the price, and repay in one transaction. Always use time-weighted average prices (TWAP) or oracle prices, never spot prices!",
        "difficulty": "Advanced",
        "points": 30,
        "stage_required": 3,
    },
    "advanced_8": {
        "question": (
            "🧩 *Puzzle A8 — Signature Replay*\n\n"
            "```solidity\n"
            "contract MetaTx {\n"
            "    function execute(bytes memory signature, address to, uint amount) public {\n"
            "        bytes32 hash = keccak256(abi.encodePacked(to, amount));\n"
            "        address signer = recover(hash, signature);\n"
            "        // transfer from signer to 'to'\n"
            "    }\n"
            "}\n"
            "```\n"
            "❓ *Question:* Can the same signature be used multiple times? (yes/no)"
        ),
        "answer": "yes",
        "explanation": "🚨 Signature replay attack! Without a nonce or expiry, the same signature can be submitted multiple times. Always include: nonce (prevents replay), chainId (prevents cross-chain replay), and expiry timestamp. Use EIP-712 for structured signatures!",
        "difficulty": "Advanced",
        "points": 30,
        "stage_required": 3,
    },
    "advanced_9": {
        "question": (
            "🧩 *Puzzle A9 — Uninitialized Storage Pointers*\n\n"
            "```solidity\n"
            "contract Storage {\n"
            "    struct User { uint id; uint balance; }\n"
            "    User[] public users;\n"
            "    \n"
            "    function addUser(uint id) public {\n"
            "        User memory user;\n"
            "        user.id = id;\n"
            "        users.push(user);\n"
            "    }\n"
            "}\n"
            "```\n"
            "❓ *Question:* What is user.balance after initialization? (number)"
        ),
        "answer": "0",
        "explanation": "In Solidity, uninitialized values default to 0. When you create 'User memory user', both id and balance are 0. Then id is set, but balance remains 0. In older Solidity versions (<0.5.0), uninitialized storage pointers could overwrite critical data!",
        "difficulty": "Advanced",
        "points": 30,
        "stage_required": 3,
    },
    "advanced_10": {
        "question": (
            "🧩 *Puzzle A10 — DOS with Block Gas Limit*\n\n"
            "```solidity\n"
            "contract Airdrop {\n"
            "    address[] public recipients;\n"
            "    \n"
            "    function distribute() public {\n"
            "        for(uint i = 0; i < recipients.length; i++) {\n"
            "            payable(recipients[i]).transfer(1 ether);\n"
            "        }\n"
            "    }\n"
            "}\n"
            "```\n"
            "❓ *Question:* Can this function fail if recipients array is too large? (yes/no)"
        ),
        "answer": "yes",
        "explanation": "🚨 Block gas limit DOS! Each block has a gas limit (~30M). If the array is too large, the loop will exceed the gas limit and ALWAYS fail. Never loop over unbounded arrays! Use pull-over-push pattern: let users withdraw instead of mass-sending.",
        "difficulty": "Advanced",
        "points": 30,
        "stage_required": 3,
    },
    # Ethernaut-Style Puzzle Pack
    # ==================== ETHERNAUT BEGINNER ====================
    "ethernaut_b1": {
        "question": (
            "🎮 *Ethernaut B1 — Fallback Function*\n\n"
            "```solidity\n"
            "contract Fallback {\n"
            "    address public owner;\n"
            "    \n"
            "    constructor() { owner = msg.sender; }\n"
            "    \n"
            "    fallback() external payable {\n"
            "        owner = msg.sender;\n"
            "    }\n"
            "}\n"
            "```\n"
            "🎯 *Mission:* Become the owner!\n\n"
            "❓ *Question:* How do you trigger the fallback function? (type the function name or 'send')"
        ),
        "answer": "send",
        "explanation": "💡 The fallback function is triggered when you send ETH to the contract without calling a specific function, or when calling a non-existent function. Just sending ETH makes you the owner! This is a common vulnerability - fallback functions should be carefully designed.",
        "difficulty": "Beginner",
        "points": 15,
        "stage_required": 1,
    },
    
    "ethernaut_b2": {
        "question": (
            "🎮 *Ethernaut B2 — Telephone*\n\n"
            "```solidity\n"
            "contract Telephone {\n"
            "    address public owner;\n"
            "    \n"
            "    function changeOwner(address _owner) public {\n"
            "        if (tx.origin != msg.sender) {\n"
            "            owner = _owner;\n"
            "        }\n"
            "    }\n"
            "}\n"
            "```\n"
            "🎯 *Mission:* Become the owner!\n\n"
            "❓ *Question:* How can tx.origin differ from msg.sender? (answer: contract/wallet)"
        ),
        "answer": "contract",
        "explanation": "💡 tx.origin is the original external account that started the transaction, while msg.sender is the immediate caller. If you call Telephone through another contract, tx.origin (you) ≠ msg.sender (your contract). Always use msg.sender for auth!",
        "difficulty": "Beginner",
        "points": 15,
        "stage_required": 1,
    },
    
    # ==================== ETHERNAUT INTERMEDIATE ====================
    "ethernaut_i1": {
        "question": (
            "🎮 *Ethernaut I1 — Token*\n\n"
            "```solidity\n"
            "contract Token {\n"
            "    mapping(address => uint) balances;\n"
            "    \n"
            "    function transfer(address _to, uint _value) public {\n"
            "        require(balances[msg.sender] - _value >= 0);\n"
            "        balances[msg.sender] -= _value;\n"
            "        balances[_to] += _value;\n"
            "    }\n"
            "}\n"
            "```\n"
            "🎯 *Mission:* Get lots of tokens!\n\n"
            "❓ *Question:* What happens if you transfer more than you have with uint? (overflow/underflow)"
        ),
        "answer": "underflow",
        "explanation": "🚨 Integer underflow! If you have 0 tokens and transfer 1, the subtraction wraps around to 2^256-1 (max uint256). The require check passes because unsigned integers can't be negative. Pre-0.8.0 Solidity had no overflow protection. This is how many tokens were hacked!",
        "difficulty": "Intermediate",
        "points": 25,
        "stage_required": 2,
    },
    
    "ethernaut_i2": {
        "question": (
            "🎮 *Ethernaut I2 — Delegation*\n\n"
            "```solidity\n"
            "contract Delegate {\n"
            "    address public owner;\n"
            "    function pwn() public { owner = msg.sender; }\n"
            "}\n\n"
            "contract Delegation {\n"
            "    address public owner;\n"
            "    Delegate delegate;\n"
            "    \n"
            "    fallback() external {\n"
            "        (bool result,) = address(delegate).delegatecall(msg.data);\n"
            "    }\n"
            "}\n"
            "```\n"
            "🎯 *Mission:* Claim ownership of Delegation!\n\n"
            "❓ *Question:* Which contract's storage is modified by delegatecall? (delegate/delegation)"
        ),
        "answer": "delegation",
        "explanation": "🚨 Delegatecall vulnerability! When Delegation uses delegatecall to Delegate, the code runs in Delegation's context. Calling pwn() through the fallback modifies Delegation's owner, not Delegate's. This is a powerful pattern but extremely dangerous with untrusted contracts!",
        "difficulty": "Intermediate",
        "points": 25,
        "stage_required": 2,
    },
    
    "ethernaut_i3": {
        "question": (
            "🎮 *Ethernaut I3 — Force*\n\n"
            "```solidity\n"
            "contract Force {/*\n\n"
            "                   MEOW ?\n"
            "         /\\_/\\   /\n"
            "    ____/ o o \\\n"
            "  /~____  =ø= /\n"
            " (______)__m_m)\n\n"
            "*/}\n"
            "```\n"
            "🎯 *Mission:* Force ETH into this empty contract!\n\n"
            "❓ *Question:* What function can send ETH to any address even without a receive function? (one word)"
        ),
        "answer": "selfdestruct",
        "explanation": "🚨 Selfdestruct force-send! Even contracts with no payable functions can receive ETH via selfdestruct. Create a contract, fund it, then selfdestruct(address(Force)). The ETH is forcibly sent. Never assume a contract's balance will be 0 or check balance for logic!",
        "difficulty": "Intermediate",
        "points": 25,
        "stage_required": 2,
    },
    
    "ethernaut_i4": {
        "question": (
            "🎮 *Ethernaut I4 — Vault*\n\n"
            "```solidity\n"
            "contract Vault {\n"
            "    bool public locked;\n"
            "    bytes32 private password;\n\n"
            "    constructor(bytes32 _password) {\n"
            "        locked = true;\n"
            "        password = _password;\n"
            "    }\n\n"
            "    function unlock(bytes32 _password) public {\n"
            "        if (password == _password) {\n"
            "            locked = false;\n"
            "        }\n"
            "    }\n"
            "}\n"
            "```\n"
            "🎯 *Mission:* Unlock the vault!\n\n"
            "❓ *Question:* Can you read private variables from the blockchain? (yes/no)"
        ),
        "answer": "yes",
        "explanation": "🚨 Nothing is private on the blockchain! The 'private' keyword only prevents other contracts from accessing the variable. Anyone can read any storage slot with web3.eth.getStorageAt(). The password is in slot 1. NEVER store secrets in smart contracts!",
        "difficulty": "Intermediate",
        "points": 25,
        "stage_required": 2,
    },
    
    # ==================== ETHERNAUT ADVANCED ====================
    "ethernaut_a1": {
        "question": (
            "🎮 *Ethernaut A1 — King*\n\n"
            "```solidity\n"
            "contract King {\n"
            "    address king;\n"
            "    uint public prize;\n\n"
            "    receive() external payable {\n"
            "        require(msg.value >= prize);\n"
            "        payable(king).transfer(prize);\n"
            "        king = msg.sender;\n"
            "        prize = msg.value;\n"
            "    }\n"
            "}\n"
            "```\n"
            "🎯 *Mission:* Become king forever (prevent others from taking over)!\n\n"
            "❓ *Question:* What happens if transfer() to old king fails? (revert/continue)"
        ),
        "answer": "revert",
        "explanation": "🚨 DOS via revert! If you become king with a contract that has no receive/fallback (or one that reverts), transfer() to you will fail when someone tries to become new king, reverting the whole transaction. You stay king forever! This is why withdrawal pattern > push payments.",
        "difficulty": "Advanced",
        "points": 35,
        "stage_required": 3,
    },
    
    "ethernaut_a2": {
        "question": (
            "🎮 *Ethernaut A2 — Re-entrancy*\n\n"
            "```solidity\n"
            "contract Reentrance {\n"
            "    mapping(address => uint) public balances;\n\n"
            "    function withdraw(uint _amount) public {\n"
            "        if(balances[msg.sender] >= _amount) {\n"
            "            (bool result,) = msg.sender.call{value: _amount}(\"\");\n"
            "            if(result) {\n"
            "                balances[msg.sender] -= _amount;\n"
            "            }\n"
            "        }\n"
            "    }\n"
            "}\n"
            "```\n"
            "🎯 *Mission:* Drain all ETH from the contract!\n\n"
            "❓ *Question:* When is the balance updated? (before/after) the external call"
        ),
        "answer": "after",
        "explanation": "🚨 Classic reentrancy! The DAO hack! Balance updates AFTER the call. Your contract's fallback can call withdraw() again before balance updates. You can withdraw repeatedly until contract is empty. Fix: Update state before external calls (CEI pattern) or use ReentrancyGuard. This hack stole $60M+!",
        "difficulty": "Advanced",
        "points": 35,
        "stage_required": 3,
    },
    
    "ethernaut_a3": {
        "question": (
            "🎮 *Ethernaut A3 — Elevator*\n\n"
            "```solidity\n"
            "interface Building {\n"
            "    function isLastFloor(uint) external returns (bool);\n"
            "}\n\n"
            "contract Elevator {\n"
            "    bool public top;\n"
            "    uint public floor;\n\n"
            "    function goTo(uint _floor) public {\n"
            "        Building building = Building(msg.sender);\n"
            "        if (!building.isLastFloor(_floor)) {\n"
            "            floor = _floor;\n"
            "            top = building.isLastFloor(floor);\n"
            "        }\n"
            "    }\n"
            "}\n"
            "```\n"
            "🎯 *Mission:* Reach the top floor!\n\n"
            "❓ *Question:* Can isLastFloor() return different values when called twice? (yes/no)"
        ),
        "answer": "yes",
        "explanation": "🚨 Interface manipulation! The contract trusts your implementation of isLastFloor(). Return false the first call (to pass the if), then true the second call (to set top=true). Never trust external contracts to behave consistently! Always validate and don't assume view functions are actually view.",
        "difficulty": "Advanced",
        "points": 35,
        "stage_required": 3,
    },
    
    "ethernaut_a4": {
        "question": (
            "🎮 *Ethernaut A4 — Privacy*\n\n"
            "```solidity\n"
            "contract Privacy {\n"
            "    bool public locked = true;\n"
            "    uint256 public ID = block.timestamp;\n"
            "    uint8 private flattening = 10;\n"
            "    uint8 private denomination = 255;\n"
            "    uint16 private awkwardness = 65535;\n"
            "    bytes32[3] private data;\n\n"
            "    function unlock(bytes16 _key) public {\n"
            "        require(_key == bytes16(data[2]));\n"
            "        locked = false;\n"
            "    }\n"
            "}\n"
            "```\n"
            "🎯 *Mission:* Unlock by finding the key!\n\n"
            "❓ *Question:* Which storage slot contains data[2]? (number 0-6)"
        ),
        "answer": "5",
        "explanation": "🚨 Storage layout: Slot 0: locked(bool). Slot 1: ID(uint256). Slot 2: flattening(uint8) + denomination(uint8) + awkwardness(uint16) packed. Slots 3,4,5: data[0], data[1], data[2]. The key is at slot 5! Storage packing is predictable. Use web3.eth.getStorageAt(address, 5) to read it!",
        "difficulty": "Advanced",
        "points": 35,
        "stage_required": 3,
    },
    
    "ethernaut_a5": {
        "question": (
            "🎮 *Ethernaut A5 — Gatekeeper One*\n\n"
            "```solidity\n"
            "contract GatekeeperOne {\n"
            "    address public entrant;\n\n"
            "    modifier gateOne() {\n"
            "        require(msg.sender != tx.origin);\n"
            "        _;\n"
            "    }\n\n"
            "    modifier gateTwo() {\n"
            "        require(gasleft() % 8191 == 0);\n"
            "        _;\n"
            "    }\n\n"
            "    function enter(bytes8 _gateKey) public gateOne gateTwo {\n"
            "        entrant = tx.origin;\n"
            "    }\n"
            "}\n"
            "```\n"
            "🎯 *Mission:* Pass all gates!\n\n"
            "❓ *Question:* What must you use to satisfy gateOne? (contract/eoa)"
        ),
        "answer": "contract",
        "explanation": "🔥 Triple challenge! Gate 1: Use a contract to call (msg.sender=contract, tx.origin=you). Gate 2: Requires exact gas calculation - you need gasleft() to be divisible by 8191. This requires trial and error or gas calculation. This combines multiple exploit techniques. Advanced Ethereum mastery required!",
        "difficulty": "Advanced",
        "points": 40,
        "stage_required": 3,
    },
}

# Organize puzzles by difficulty for random selection
PUZZLES_BY_DIFFICULTY = {
    "Beginner": [k for k, v in PUZZLES.items() if v["difficulty"] == "Beginner"],
    "Intermediate": [k for k, v in PUZZLES.items() if v["difficulty"] == "Intermediate"],
    "Advanced": [k for k, v in PUZZLES.items() if v["difficulty"] == "Advanced"],
}

# Stage requirements: how many puzzles needed to unlock next stage
STAGE_REQUIREMENTS = {
    1: 0,   # Stage 1 unlocked by default
    2: 3,   # Need 3 beginner puzzles to unlock intermediate
    3: 7,   # Need 7 total puzzles (3 beginner + 4 intermediate) to unlock advanced
}

# Awards for milestones
AWARDS = {
    "first_solve": {
        "name": "🎯 First Blood", 
        "description": "Solved your first puzzle",
        "points_bonus": 5
    },
    "beginner_master": {
        "name": "🟢 Beginner Master", 
        "description": "Completed all beginner puzzles",
        "points_bonus": 20
    },
    "intermediate_master": {
        "name": "🟡 Intermediate Master", 
        "description": "Completed all intermediate puzzles",
        "points_bonus": 40
    },
    "advanced_master": {
        "name": "🔴 Advanced Master", 
        "description": "Completed all advanced puzzles",
        "points_bonus": 60
    },
    "speedrun_3": {
        "name": "⚡ Speed Demon", 
        "description": "Solved 3 puzzles in under 15 minutes",
        "points_bonus": 30
    },
    "speedrun_5": {
        "name": "⚡⚡ Lightning Fast", 
        "description": "Solved 5 puzzles in under 30 minutes",
        "points_bonus": 50
    },
    "perfect_streak_5": {
        "name": "💯 Perfect Streak", 
        "description": "Solved 5 puzzles without wrong answers",
        "points_bonus": 35
    },
    "perfect_streak_10": {
        "name": "💯💯 Flawless Victory", 
        "description": "Solved 10 puzzles without wrong answers",
        "points_bonus": 75
    },
    "grand_master": {
        "name": "👑 Grand Master", 
        "description": "Completed ALL puzzles",
        "points_bonus": 100
    },
    "security_expert": {
        "name": "🛡️ Security Expert",
        "description": "Solved all advanced security puzzles (reentrancy, delegatecall, etc.)",
        "points_bonus": 50
    },
    "night_owl": {
        "name": "🦉 Night Owl",
        "description": "Solved puzzles between midnight and 5 AM",
        "points_bonus": 15
    },
    "early_bird": {
        "name": "🌅 Early Bird",
        "description": "Solved puzzles between 5 AM and 8 AM",
        "points_bonus": 15
    },
    "comeback_king": {
        "name": "👑 Comeback King",
        "description": "Got 5 wrong answers but kept trying and solved it",
        "points_bonus": 25
    },
    "ten_in_row": {
        "name": "🔥 On Fire",
        "description": "Solved 10 puzzles in a single session",
        "points_bonus": 40
    },
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome user and ask for username if missing."""
    user_id = update.effective_user.id
    name = get_username(user_id)
    if not name:
        USER_NAME_PENDING.add(user_id)
        await update.message.reply_text(
            "🎮 *Welcome to Smart Contract Puzzle Lab!*\n\n"
            "Test your Solidity skills through challenging puzzles.\n"
            "Find vulnerabilities, understand patterns, and master smart contract security!\n\n"
            "Before we begin, please enter your username:",
            parse_mode="Markdown"
        )
    else:
        await show_menu_message(update)


async def show_awards_callback(query):
    """Display user's earned awards."""
    user_id = query.from_user.id
    awards = get_user_awards(user_id)
    name = get_username(user_id)
    
    if not awards:
        await query.edit_message_text(
            f"🎁 *{name or 'Player'}'s Awards*\n\n"
            f"No awards yet! Keep solving puzzles to earn achievements.",
            parse_mode="Markdown"
        )
        return
    
    award_text = ""
    for award_key in awards:
        if award_key in AWARDS:
            award_text += f"{AWARDS[award_key]['name']}\n_{AWARDS[award_key]['description']}_\n\n"
    
    await query.edit_message_text(
        f"🎁 *{name or 'Player'}'s Awards*\n\n{award_text}",
        parse_mode="Markdown"
    )


async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to show progress."""
    user_id = update.effective_user.id
    solved, score, difficulty_scores, name = get_user_progress(user_id)
    stage = get_user_stage(user_id)
    awards = get_user_awards(user_id)
    
    progress_text = ""
    for diff in ["Beginner", "Intermediate", "Advanced"]:
        total = len(PUZZLES_BY_DIFFICULTY[diff])
        solved_in_diff = len([p for p in solved if p in PUZZLES_BY_DIFFICULTY[diff]])
        progress_text += f"{diff}: {solved_in_diff}/{total}\n"
    
    text = (
        f"📊 *{name or 'Player'}'s Progress*\n\n"
        f"🎯 Stage: *{stage}*\n"
        f"⭐ Total Score: *{score}*\n"
        f"✅ Puzzles Solved: *{len(solved)}/{len(PUZZLES)}*\n\n"
        f"*By Difficulty:*\n{progress_text}\n"
        f"🏆 Awards: *{len(awards)}*"
    )
    
    await update.message.reply_text(text, parse_mode="Markdown")


async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show leaderboard with optional difficulty filter."""
    args = context.args
    difficulty = None
    if args:
        candidate = args[0].capitalize()
        if candidate in ["Beginner", "Intermediate", "Advanced"]:
            difficulty = candidate
    
    board = get_leaderboard(top_n=10, difficulty=difficulty)
    
    if not board or all(score == 0 for _, score in board):
        await update.message.reply_text(
            f"🏆 No scores yet for {difficulty or 'Overall'} leaderboard.\nBe the first to solve some puzzles!",
            parse_mode="Markdown"
        )
        return
    
    text = f"🏆 *{difficulty or 'Overall'} Leaderboard*\n\n"
    for i, (name, score) in enumerate(board, start=1):
        # fixed conditional expression (was missing 'else' parts)
        medal = "🥇" if i == 1 else ("🥈" if i == 2 else ("🥉" if i == 3 else f"{i}."))
        text += f"{medal} {name} — *{score}* pts\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")


async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback variant of leaderboard."""
    query = update.callback_query
    await query.answer()
    data = query.data
    
    diff = None
    if data == "leaderboard_beginner":
        diff = "Beginner"
    elif data == "leaderboard_intermediate":
        diff = "Intermediate"
    elif data == "leaderboard_advanced":
        diff = "Advanced"
    elif data == "leaderboard_overall":
        diff = None
    
    board = get_leaderboard(top_n=10, difficulty=diff)
    
    if not board or all(score == 0 for _, score in board):
        await query.edit_message_text(
            f"🏆 No scores yet for {diff or 'Overall'} leaderboard.\nBe the first!",
            parse_mode="Markdown"
        )
        return
    
    text = f"🏆 *{diff or 'Overall'} Leaderboard*\n\n"
    for i, (name, score) in enumerate(board, start=1):
        # fixed conditional expression (was missing 'else' parts)
        medal = "🥇" if i == 1 else ("🥈" if i == 2 else ("🥉" if i == 3 else f"{i}."))
        text += f"{medal} {name} — *{score}* pts\n"
    
    await query.edit_message_text(text, parse_mode="Markdown")


def register_handlers(application):
    """Register all handlers on the application."""
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    logger.info("Registered /start")
    
    application.add_handler(CommandHandler("menu", menu_command))
    logger.info("Registered /menu")
    
    application.add_handler(CommandHandler("progress", progress_command))
    logger.info("Registered /progress")
    
    application.add_handler(CommandHandler("leaderboard", leaderboard_command))
    logger.info("Registered /leaderboard")
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(difficulty_select_callback, pattern="^difficulty_|^show_progress|^choose_leaderboard|^show_awards|^locked_"))
    logger.info("Registered difficulty and menu callbacks")
    
    application.add_handler(CallbackQueryHandler(start_puzzle_callback, pattern="^start_|^random_"))
    logger.info("Registered puzzle start callbacks")
    
    application.add_handler(CallbackQueryHandler(show_answer_callback, pattern="^answer_"))
    logger.info("Registered show answer callbacks")
    
    application.add_handler(CallbackQueryHandler(leaderboard_callback, pattern="^leaderboard_"))
    logger.info("Registered leaderboard callbacks")
    
    # Text message handler
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), receive_message))
    logger.info("Registered text message handler")

    # Admin command handlers
    application.add_handler(CommandHandler("stats", cmd_admin_stats))
    application.add_handler(CommandHandler("dumpdata", cmd_dump))
    application.add_handler(CommandHandler("userstats", cmd_user))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome user and ask for username if missing."""
    user_id = update.effective_user.id
    name = get_username(user_id)
    if not name:
        USER_NAME_PENDING.add(user_id)
        await update.message.reply_text(
            "🎮 *Welcome to Smart Contract Puzzle Lab!*\n\n"
            "Test your Solidity skills through challenging puzzles.\n"
            "Find vulnerabilities, understand patterns, and master smart contract security!\n\n"
            "Before we begin, please enter your username:",
            parse_mode="Markdown"
        )
    else:
        await show_menu_message(update)


async def show_menu_message(update_or_ctx, context: ContextTypes.DEFAULT_TYPE = None):
    """Send the main menu with stage-based access."""
    if isinstance(update_or_ctx, Update):
        update = update_or_ctx
    else:
        update = update_or_ctx
    
    user_id = update.effective_user.id if hasattr(update, 'effective_user') else update.callback_query.from_user.id
    stage = get_user_stage(user_id)
    solved_count = len(get_user_progress(user_id)[0])
    
    # Build keyboard based on unlocked stages
    keyboard = []
    
    # Stage 1: Beginner (always unlocked)
    keyboard.append([InlineKeyboardButton("🟢 Beginner (Stage 1)", callback_data="difficulty_beginner")])
    
    # Stage 2: Intermediate (unlock after 2 puzzles)
    if stage >= 2:
        keyboard.append([InlineKeyboardButton("🟡 Intermediate (Stage 2)", callback_data="difficulty_intermediate")])
    else:
        needed = STAGE_REQUIREMENTS[2] - solved_count
        keyboard.append([InlineKeyboardButton(f"🔒 Intermediate (Solve {needed} more)", callback_data="locked_2")])
    
    # Stage 3: Advanced (unlock after 4 puzzles)
    if stage >= 3:
        keyboard.append([InlineKeyboardButton("🔴 Advanced (Stage 3)", callback_data="difficulty_advanced")])
    else:
        needed = STAGE_REQUIREMENTS[3] - solved_count
        keyboard.append([InlineKeyboardButton(f"🔒 Advanced (Solve {needed} more)", callback_data="locked_3")])
    
    keyboard.append([InlineKeyboardButton("📊 My Progress", callback_data="show_progress")])
    keyboard.append([InlineKeyboardButton("🏆 Leaderboard", callback_data="choose_leaderboard")])
    keyboard.append([InlineKeyboardButton("🎁 My Awards", callback_data="show_awards")])
    
    menu_text = (
        f"🎮 *Main Menu*\n\n"
        f"Current Stage: *{stage}*\n"
        f"Puzzles Solved: *{solved_count}*\n\n"
        f"Choose your challenge:"
    )
    
    if update.callback_query:
        await update.callback_query.message.reply_text(
            menu_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            menu_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle free-text messages for username or puzzle answers."""
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # Username setup flow
    if user_id in USER_NAME_PENDING:
        name = text[:40]
        set_username(user_id, name)
        USER_NAME_PENDING.remove(user_id)
        
        # Check for first solve award
        solved_count = len(get_user_progress(user_id)[0])
        if solved_count == 0:
            await update.message.reply_text(
                f"✅ Welcome, *{name}*!\n\n"
                f"You're ready to start your journey. Use /menu to begin!",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(f"✅ Username updated to *{name}*! Use /menu to continue.", parse_mode="Markdown")
        return

    # Puzzle attempt flow
    current = context.user_data.get("current_puzzle")
    if current:
        puzzle_id = current
        expected = PUZZLES[puzzle_id]["answer"]
        
        # Flexible answer matching
        user_answer = str(text).strip().lower()
        correct_answer = str(expected).strip().lower()
        
        if user_answer == correct_answer:
            # Correct answer
            mark_puzzle_solved(user_id, puzzle_id, correct=True)
            context.user_data.pop("current_puzzle", None)
            
            points = PUZZLES[puzzle_id]["points"]
            difficulty = PUZZLES[puzzle_id]["difficulty"]
            
            # Check for stage advancement
            solved_count = len(get_user_progress(user_id)[0])
            old_stage = get_user_stage(user_id)
            new_stage = advance_user_stage(user_id)
            
            response = f"✅ *Correct!*\n\n+{points} points earned!\n\n"
            response += f"📘 *Explanation:*\n{PUZZLES[puzzle_id]['explanation']}\n\n"
            
            # Check for awards
            awards_earned = []
            if solved_count == 1:
                record_award(user_id, "first_solve")
                awards_earned.append("first_solve")
                response += f"🎁 *Achievement Unlocked:* {AWARDS['first_solve']['name']}\n"
                response += f"_+{AWARDS['first_solve']['points_bonus']} bonus points!_\n\n"
            
            # Check difficulty mastery
            difficulty_puzzles = PUZZLES_BY_DIFFICULTY[difficulty]
            difficulty_solved = [p for p in get_user_progress(user_id)[0] if p in difficulty_puzzles]
            if len(difficulty_solved) == len(difficulty_puzzles):
                award_key = f"{difficulty.lower()}_master"
                if award_key in AWARDS and not is_award_earned(user_id, award_key):
                    record_award(user_id, award_key)
                    awards_earned.append(award_key)
                    response += f"🎁 *Achievement Unlocked:* {AWARDS[award_key]['name']}\n"
                    response += f"_+{AWARDS[award_key]['points_bonus']} bonus points!_\n\n"
            
            # Check grand master
            if solved_count == len(PUZZLES):
                if not is_award_earned(user_id, "grand_master"):
                    record_award(user_id, "grand_master")
                    awards_earned.append("grand_master")
                    response += f"👑 *LEGENDARY ACHIEVEMENT:* {AWARDS['grand_master']['name']}\n"
                    response += f"_+{AWARDS['grand_master']['points_bonus']} bonus points!_\n\n"
            
            # Check perfect streak (no wrong answers)
            last_wrong_for_puzzle = get_last_wrong(user_id, puzzle_id)
            # if there's no recorded wrong attempt for this user/puzzle, treat as perfect
            if not last_wrong_for_puzzle:
                 perfect_count = get_perfect_solve_count(user_id)
                 if perfect_count >= 10 and not is_award_earned(user_id, "perfect_streak_10"):
                     record_award(user_id, "perfect_streak_10")
                     awards_earned.append("perfect_streak_10")
                     response += f"💯💯 *Achievement:* {AWARDS['perfect_streak_10']['name']}\n"
                     response += f"_+{AWARDS['perfect_streak_10']['points_bonus']} bonus points!_\n\n"
                 elif perfect_count >= 5 and not is_award_earned(user_id, "perfect_streak_5"):
                     record_award(user_id, "perfect_streak_5")
                     awards_earned.append("perfect_streak_5")
                     response += f"💯 *Achievement:* {AWARDS['perfect_streak_5']['name']}\n"
                     response += f"_+{AWARDS['perfect_streak_5']['points_bonus']} bonus points!_\n\n"
            
            # Check time-based awards
            from datetime import datetime
            current_hour = datetime.now().hour
            if 0 <= current_hour < 5 and not is_award_earned(user_id, "night_owl"):
                record_award(user_id, "night_owl")
                awards_earned.append("night_owl")
                response += f"🦉 *Achievement:* {AWARDS['night_owl']['name']}\n"
                response += f"_+{AWARDS['night_owl']['points_bonus']} bonus points!_\n\n"
            elif 5 <= current_hour < 8 and not is_award_earned(user_id, "early_bird"):
                record_award(user_id, "early_bird")
                awards_earned.append("early_bird")
                response += f"🌅 *Achievement:* {AWARDS['early_bird']['name']}\n"
                response += f"_+{AWARDS['early_bird']['points_bonus']} bonus points!_\n\n"
            
            # Award bonus points
            if awards_earned:
                total_bonus = sum(AWARDS[a]["points_bonus"] for a in awards_earned if a in AWARDS)
                if total_bonus > 0:
                    add_bonus_points(user_id, total_bonus)
            
            # Stage advancement notification
            if new_stage > old_stage:
                response += f"🎉 *STAGE UP!* You've unlocked Stage {new_stage}!\n\n"
            
            await update.message.reply_text(response, parse_mode="Markdown")
        else:
            # Incorrect answer
            record_wrong_answer(user_id, puzzle_id, text)
            await update.message.reply_text(
                "❌ *Incorrect.*\n\n"
                "Try again or press *Show Answer* to see the solution.",
                parse_mode="Markdown"
            )
        return

    await update.message.reply_text("Use /menu to choose a puzzle or /progress to see your stats!")


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command handler for /menu."""
    user_id = update.effective_user.id
    if not get_username(user_id):
        USER_NAME_PENDING.add(user_id)
        await update.message.reply_text("Please enter your username first:")
        return
    await show_menu_message(update)


async def difficulty_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle difficulty selection and locked stages."""
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    
    # Handle locked stages
    if data.startswith("locked_"):
        stage_num = int(data.split("_")[1])
        needed = STAGE_REQUIREMENTS[stage_num] - len(get_user_progress(user_id)[0])
        await query.answer(f"🔒 Solve {needed} more puzzle(s) to unlock this stage!", show_alert=True)
        return
    
    if data == "difficulty_beginner":
        await query.edit_message_text("🟢 *Beginner Puzzles*\n\nPick a puzzle or get a random one:", parse_mode="Markdown")
        await send_puzzle_list(query, "Beginner", user_id)
    elif data == "difficulty_intermediate":
        await query.edit_message_text("🟡 *Intermediate Puzzles*\n\nPick a puzzle or get a random one:", parse_mode="Markdown")
        await send_puzzle_list(query, "Intermediate", user_id)
    elif data == "difficulty_advanced":
        await query.edit_message_text("🔴 *Advanced Puzzles*\n\nPick a puzzle or get a random one:", parse_mode="Markdown")
        await send_puzzle_list(query, "Advanced", user_id)
    elif data == "show_progress":
        await show_progress_callback(query)
    elif data == "choose_leaderboard":
        kb = [
            [InlineKeyboardButton("Beginner", callback_data="leaderboard_beginner")],
            [InlineKeyboardButton("Intermediate", callback_data="leaderboard_intermediate")],
            [InlineKeyboardButton("Advanced", callback_data="leaderboard_advanced")],
            [InlineKeyboardButton("Overall", callback_data="leaderboard_overall")],
        ]
        await query.edit_message_text("🏆 *Choose Leaderboard:*", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    elif data == "show_awards":
        await show_awards_callback(query)


async def send_puzzle_list(callback_query, difficulty_name: str, user_id: int):
    """Send list of puzzles for a difficulty with random option."""
    puzzles = PUZZLES_BY_DIFFICULTY.get(difficulty_name, [])
    if not puzzles:
        await callback_query.message.reply_text(f"No puzzles available for {difficulty_name}.")
        return
    
    keyboard = []
    
    # Add random puzzle button at top
    keyboard.append([InlineKeyboardButton("🎲 Random Unsolved Puzzle", callback_data=f"random_{difficulty_name.lower()}")])
    
    # Add individual puzzles with solved status
    for p in puzzles:
        solved = is_puzzle_solved(user_id, p)
        emoji = "✅" if solved else "❓"
        display_name = PUZZLES[p].get("question", "").split("—")[1].split("*")[0].strip() if "—" in PUZZLES[p].get("question", "") else p
        keyboard.append([InlineKeyboardButton(f"{emoji} {display_name}", callback_data=f"start_{p}")])
    
    await callback_query.message.reply_text(
        f"*{difficulty_name} Puzzles:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def start_puzzle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle puzzle start including random selection."""
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    
    # Handle random puzzle selection
    if data.startswith("random_"):
        difficulty = data.split("random_")[1].capitalize()
        puzzle_id = get_random_unsolved_puzzle(user_id, difficulty)
        
        if not puzzle_id:
            await query.answer("🎉 You've solved all puzzles in this difficulty!", show_alert=True)
            return
    else:
        # Regular puzzle selection
        puzzle_id = data.split("start_")[1] if data.startswith("start_") else data
    
    if puzzle_id not in PUZZLES:
        await query.edit_message_text("❌ Invalid puzzle.")
        return
    
    # Send puzzle question with Show Answer button
    kb = [[InlineKeyboardButton("💡 Show Answer", callback_data=f"answer_{puzzle_id}")]]
    await query.message.reply_text(
        PUZZLES[puzzle_id]["question"],
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )
    
    # Set active puzzle
    context.user_data["current_puzzle"] = puzzle_id


async def show_answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show answer with user's wrong attempt if any."""
    query = update.callback_query
    await query.answer()
    data = query.data
    puzzle_id = data.split("answer_")[1] if data.startswith("answer_") else data.split("_")[-1]
    
    if puzzle_id not in PUZZLES:
        await query.edit_message_text("❌ Couldn't find answer.")
        return
    
    user_id = query.from_user.id
    correct = PUZZLES[puzzle_id]["answer"]
    explanation = PUZZLES[puzzle_id]["explanation"]
    last_wrong = get_last_wrong(user_id, puzzle_id)
    
    if last_wrong:
        text = (
            f"❌ *Your answer:* `{last_wrong}`\n"
            f"✅ *Correct answer:* `{correct}`\n\n"
            f"📘 *Explanation:*\n{explanation}\n\n"
            f"_No points awarded for viewing the answer._"
        )
    else:
        text = (
            f"✅ *Correct answer:* `{correct}`\n\n"
            f"📘 *Explanation:*\n{explanation}\n\n"
            f"_No points awarded for viewing the answer._"
        )
    
    await query.edit_message_text(text, parse_mode="Markdown")
    
    # Clear current puzzle
    if "current_puzzle" in query._context.user_data:
        query._context.user_data.pop("current_puzzle")


async def show_progress_callback(query):
    """Show user progress with stage info."""
    user_id = query.from_user.id
    solved, score, difficulty_scores, name = get_user_progress(user_id)
    stage = get_user_stage(user_id)
    awards = get_user_awards(user_id)
    
    # Calculate progress by difficulty
    progress_text = ""
    for diff in ["Beginner", "Intermediate", "Advanced"]:
        total = len(PUZZLES_BY_DIFFICULTY[diff])
        solved_in_diff = len([p for p in solved if p in PUZZLES_BY_DIFFICULTY[diff]])
        progress_text += f"{diff}: {solved_in_diff}/{total}\n"
    
    text = (
        f"📊 *{name or 'Player'}'s Progress*\n\n"
        f"🎯 Stage: *{stage}*\n"
        f"⭐ Total Score: *{score}*\n"
        f"✅ Puzzles Solved: *{len(solved)}/{len(PUZZLES)}*\n\n"
        f"*By Difficulty:*\n{progress_text}\n"
        f"🏆 Awards: *{len(awards)}*"
    )
    
    await query.edit_message_text(text, parse_mode="Markdown")