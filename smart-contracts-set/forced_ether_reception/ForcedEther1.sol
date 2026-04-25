// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

/// @title ForcedEther1 - Contract logic broken by forced ETH via selfdestruct
/// @notice Assumes this.balance only changes via deposit() — wrong assumption
contract ForcedEther1 {
    address public owner;
    uint256 public jackpot;
    address[] public players;

    constructor() public payable {
        owner = msg.sender;
        jackpot = msg.value;
    }

    function enter() public payable {
        require(msg.value == 1 ether, "Must send exactly 1 ETH");
        players.push(msg.sender);
    }

    /// @notice BAD: an attacker can selfdestruct another contract into this one
    /// forcing address(this).balance above jackpot without entering — breaking game logic
    function checkWin() public {
        // BAD: this.balance can be forced higher than jackpot via selfdestruct
        if (address(this).balance == jackpot * 2) {
            msg.sender.transfer(address(this).balance);
        }
    }

    function getPlayerCount() public view returns (uint256) {
        return players.length;
    }
}
