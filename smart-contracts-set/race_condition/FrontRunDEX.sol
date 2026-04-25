// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

/// @title FrontRunDEX - Race condition in a simple token swap (front-running)
/// @notice Miner or bot sees pending tx and inserts their own tx first to profit
contract FrontRunDEX {
    address public owner;
    mapping(address => uint256) public tokenBalances;
    mapping(address => uint256) public ethBalances;
    uint256 public tokenPrice; // price in wei per token

    event Trade(address indexed trader, uint256 tokens, uint256 ethPaid);
    event PriceUpdated(uint256 newPrice);

    constructor(uint256 initialPrice) public payable {
        owner = msg.sender;
        tokenPrice = initialPrice;
        tokenBalances[owner] = 10000;
    }

    /// @notice BAD: owner updates price in mempool — front-runner buys before update
    function updatePrice(uint256 newPrice) public {
        require(msg.sender == owner, "Only owner");
        tokenPrice = newPrice; // visible in mempool before execution
        emit PriceUpdated(newPrice);
    }

    /// @notice Buy tokens — susceptible to sandwich attack
    function buyTokens(uint256 amount) public payable {
        require(msg.value == amount * tokenPrice, "Incorrect ETH");
        require(tokenBalances[owner] >= amount, "Not enough tokens");
        tokenBalances[owner] -= amount;
        tokenBalances[msg.sender] += amount;
        emit Trade(msg.sender, amount, msg.value);
    }

    function sellTokens(uint256 amount) public {
        require(tokenBalances[msg.sender] >= amount, "Insufficient tokens");
        uint256 payout = amount * tokenPrice;
        tokenBalances[msg.sender] -= amount;
        tokenBalances[owner] += amount;
        msg.sender.transfer(payout);
        emit Trade(msg.sender, amount, payout);
    }

    function deposit() public payable {
        ethBalances[msg.sender] += msg.value;
    }
}
