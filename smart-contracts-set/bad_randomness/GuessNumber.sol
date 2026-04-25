// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

/// @title GuessNumber - Bad randomness using blockhash and block.number
/// @notice Players guess a number; winner is determined by blockhash (predictable)
contract GuessNumber {
    uint256 public answer;
    address public lastWinner;
    uint256 public prize;

    event Winner(address winner, uint256 prize);

    constructor() public payable {
        prize = msg.value;
        // BAD: blockhash is known to miners in the same block
        answer = uint256(blockhash(block.number - 1)) % 10;
    }

    function guess(uint256 number) public payable {
        require(msg.value >= 0.01 ether, "Min bet required");
        // BAD: block.number used for randomness
        uint256 random = uint256(blockhash(block.number - 1)) % 10;
        if (number == random) {
            lastWinner = msg.sender;
            uint256 reward = address(this).balance;
            msg.sender.transfer(reward);
            emit Winner(msg.sender, reward);
        }
    }

    function refreshAnswer() public {
        // BAD: now is an alias for block.timestamp
        answer = uint256(now) % 10;
    }
}
