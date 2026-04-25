// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title SafeWithdraw - Demonstrates the pull-payment pattern (safe withdrawal)
/// @notice Uses Checks-Effects-Interactions pattern to prevent reentrancy
contract SafeWithdraw {
    address public owner;
    mapping(address => uint256) public balances;

    event Deposited(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    /// @notice Users deposit ETH credited to their account
    function deposit() external payable {
        require(msg.value > 0, "No ETH sent");
        balances[msg.sender] += msg.value;
        emit Deposited(msg.sender, msg.value);
    }

    /// @notice Pull-payment: user withdraws their own balance (CEI pattern)
    function withdraw() external {
        uint256 amount = balances[msg.sender];
        require(amount > 0, "Nothing to withdraw");

        // CHECKS
        require(address(this).balance >= amount, "Contract underfunded");

        // EFFECTS — update state BEFORE external call
        balances[msg.sender] = 0;

        // INTERACTIONS — external call last
        (bool success, ) = payable(msg.sender).call{value: amount}("");
        require(success, "Transfer failed");

        emit Withdrawn(msg.sender, amount);
    }

    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }

    function ownerWithdraw() external onlyOwner {
        uint256 amount = address(this).balance;
        require(amount > 0, "Nothing to withdraw");
        (bool success, ) = payable(owner).call{value: amount}("");
        require(success, "Transfer failed");
    }
}
