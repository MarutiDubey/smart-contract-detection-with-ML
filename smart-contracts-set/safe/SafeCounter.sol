// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title SafeCounter - Overflow-safe counter using Solidity 0.8+ built-in checks
contract SafeCounter {
    uint256 public count;
    address public owner;

    event Incremented(address indexed by, uint256 newCount);
    event Reset(address indexed by);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner");
        _;
    }

    constructor() {
        owner = msg.sender;
        count = 0;
    }

    function increment() external {
        count += 1; // Safe: Solidity 0.8+ reverts on overflow
        emit Incremented(msg.sender, count);
    }

    function incrementBy(uint256 amount) external {
        require(amount > 0 && amount <= 1000, "Amount out of range");
        count += amount;
        emit Incremented(msg.sender, count);
    }

    function reset() external onlyOwner {
        count = 0;
        emit Reset(msg.sender);
    }

    function getCount() external view returns (uint256) {
        return count;
    }
}
