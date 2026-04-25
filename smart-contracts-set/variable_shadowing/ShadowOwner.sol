// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

/// @title ShadowOwner - State variable shadowing ownership across contracts
/// @notice Derived contract redefines `owner`, breaking parent's authorization logic
contract Ownable {
    address public owner;

    constructor() public {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    function transferOwnership(address newOwner) public onlyOwner {
        owner = newOwner;
    }
}

/// @notice BAD: redeclares `owner` — shadows parent's owner, causing split ownership state
contract ShadowOwner is Ownable {
    address public owner; // SHADOWING: this is a different variable than Ownable.owner!
    uint256 public funds;

    constructor() public {
        owner = msg.sender; // sets ShadowOwner.owner, NOT Ownable.owner
    }

    /// @notice Uses Ownable.onlyOwner which checks Ownable.owner — NOT ShadowOwner.owner
    function withdrawFunds() public onlyOwner {
        msg.sender.transfer(funds);
    }

    function deposit() public payable {
        funds += msg.value;
    }
}
