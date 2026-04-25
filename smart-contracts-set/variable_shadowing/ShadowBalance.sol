// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

/// @title ShadowBalance - Local variable shadows state variable (SWC-119)
/// @notice Local `balance` in function shadows the storage `balance` mapping
contract ShadowBalance {
    mapping(address => uint256) public balance; // state variable

    event Deposited(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);

    function deposit() public payable {
        balance[msg.sender] += msg.value;
        emit Deposited(msg.sender, msg.value);
    }

    /// @notice BAD: local variable `balance` shadows state variable `balance`
    function withdraw(uint256 amount) public {
        uint256 balance = balance[msg.sender]; // local shadows state var — confusing!
        require(balance >= amount, "Insufficient");

        // State is updated via the local reference — may not correctly reflect
        balance -= amount; // only modifies local copy, NOT balance[msg.sender]!
        msg.sender.transfer(amount);

        emit Withdrawn(msg.sender, amount);
        // balance[msg.sender] unchanged — attacker can withdraw unlimited times
    }

    function getBalance(address user) public view returns (uint256) {
        return balance[user];
    }
}
