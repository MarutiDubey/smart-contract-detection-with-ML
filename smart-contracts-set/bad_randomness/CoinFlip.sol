// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

/// @title BadRandom1 - Bad randomness via block.timestamp
/// @notice Attacker can predict the "winner" by manipulating block timing
contract CoinFlip {
    address public owner;
    uint256 public pot;

    constructor() public payable {
        owner = msg.sender;
        pot = msg.value;
    }

    /// @notice Guess heads (true) or tails (false)
    function flip(bool guess) public payable {
        require(msg.value > 0, "Send ETH to play");
        bool result = (block.timestamp % 2 == 0); // BAD: miner-controllable
        if (result == guess) {
            uint256 winnings = msg.value * 2;
            pot += msg.value;
            msg.sender.transfer(winnings);
        } else {
            pot += msg.value;
        }
    }

    function drainPot() public {
        require(msg.sender == owner);
        owner.transfer(address(this).balance);
    }
}
