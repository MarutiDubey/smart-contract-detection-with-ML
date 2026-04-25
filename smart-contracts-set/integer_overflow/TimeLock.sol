// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

/// @title TimeLock - Overflow in timestamp comparison (batch overflow pattern)
/// @notice lockTime can be overflowed to unlock funds immediately
contract TimeLock {
    mapping(address => uint256) public balances;
    mapping(address => uint256) public lockTime;

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        // Lock for 1 week
        lockTime[msg.sender] = now + 1 weeks;
    }

    // BAD: attacker can pass a huge value causing lockTime to overflow to a small number
    function increaseLockTime(uint256 secondsToIncrease) public {
        lockTime[msg.sender] += secondsToIncrease; // OVERFLOW: wraps around 2^256
    }

    function withdraw() public {
        require(balances[msg.sender] > 0, "No balance");
        require(now > lockTime[msg.sender], "Funds locked"); // bypassed after overflow
        uint256 amount = balances[msg.sender];
        balances[msg.sender] = 0;
        msg.sender.transfer(amount);
    }
}
