// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

/// @title Lottery - Bad randomness using keccak256 of on-chain data
/// @notice All inputs (block.difficulty, block.timestamp, participants) are public
contract Lottery {
    address[] public participants;
    address public manager;
    uint256 public ticketPrice;

    event TicketBought(address indexed buyer);
    event WinnerPicked(address indexed winner, uint256 prize);

    constructor() public payable {
        manager = msg.sender;
        ticketPrice = 0.01 ether;
    }

    function enter() public payable {
        require(msg.value == ticketPrice, "Wrong ticket price");
        participants.push(msg.sender);
        emit TicketBought(msg.sender);
    }

    function pickWinner() public {
        require(msg.sender == manager, "Manager only");
        require(participants.length >= 3, "Need more players");

        // BAD: all inputs are deterministic and visible on-chain
        uint256 index = uint256(
            keccak256(
                abi.encodePacked(block.difficulty, block.timestamp, participants)
            )
        ) % participants.length;

        address winner = participants[index];
        uint256 prize = address(this).balance;

        winner.transfer(prize);
        participants = new address[](0);

        emit WinnerPicked(winner, prize);
    }

    function getParticipants() public view returns (address[]) {
        return participants;
    }
}
