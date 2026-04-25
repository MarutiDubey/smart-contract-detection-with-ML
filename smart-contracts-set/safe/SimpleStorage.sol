// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title SimpleStorage - A safe, basic storage contract
/// @notice Demonstrates safe state management with owner access control
contract SimpleStorage {
    address public owner;
    uint256 private storedValue;

    event ValueChanged(address indexed by, uint256 newValue);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not authorized");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function set(uint256 value) external onlyOwner {
        storedValue = value;
        emit ValueChanged(msg.sender, value);
    }

    function get() external view returns (uint256) {
        return storedValue;
    }
}
