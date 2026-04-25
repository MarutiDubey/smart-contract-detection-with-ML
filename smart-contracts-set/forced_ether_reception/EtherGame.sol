// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

/// @title EtherGame - Targetting exact balance broken by forced ETH (SWC-132)
/// @notice Anyone can use selfdestruct to force ETH into contract and DoS the game
contract EtherGame {
    uint256 public targetAmount = 5 ether;
    address public winner;

    function deposit() public payable {
        // BAD: strict equality on balance — easily broken by forced ETH
        require(address(this).balance <= targetAmount, "Game over");
    }

    /// @notice BAD: once balance is forced past targetAmount, claimReward is unreachable
    function claimReward() public {
        require(address(this).balance == targetAmount, "Not at target"); // can NEVER be true after force
        require(winner == address(0), "Winner set");
        winner = msg.sender;
        msg.sender.transfer(address(this).balance);
    }

    function getBalance() public view returns (uint256) {
        return address(this).balance;
    }
}
