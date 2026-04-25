// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Voting - A safe, transparent on-chain voting contract
/// @notice Prevents double voting, uses explicit access control
contract Voting {
    struct Candidate {
        string name;
        uint256 voteCount;
    }

    address public chairperson;
    mapping(address => bool) public hasVoted;
    Candidate[] public candidates;
    bool public votingOpen;

    event VoteCast(address indexed voter, uint256 candidateIndex);
    event VotingStarted();
    event VotingEnded();

    modifier onlyChair() {
        require(msg.sender == chairperson, "Only chairperson");
        _;
    }

    modifier onlyWhenOpen() {
        require(votingOpen, "Voting is closed");
        _;
    }

    constructor(string[] memory candidateNames) {
        chairperson = msg.sender;
        votingOpen = false;
        for (uint256 i = 0; i < candidateNames.length; i++) {
            candidates.push(Candidate({ name: candidateNames[i], voteCount: 0 }));
        }
    }

    function startVoting() external onlyChair {
        votingOpen = true;
        emit VotingStarted();
    }

    function endVoting() external onlyChair {
        votingOpen = false;
        emit VotingEnded();
    }

    function vote(uint256 candidateIndex) external onlyWhenOpen {
        require(!hasVoted[msg.sender], "Already voted");
        require(candidateIndex < candidates.length, "Invalid candidate");

        hasVoted[msg.sender] = true;
        candidates[candidateIndex].voteCount += 1;

        emit VoteCast(msg.sender, candidateIndex);
    }

    function getWinner() external view returns (string memory winnerName, uint256 winnerVotes) {
        uint256 winIdx = 0;
        for (uint256 i = 1; i < candidates.length; i++) {
            if (candidates[i].voteCount > candidates[winIdx].voteCount) {
                winIdx = i;
            }
        }
        return (candidates[winIdx].name, candidates[winIdx].voteCount);
    }

    function candidatesCount() external view returns (uint256) {
        return candidates.length;
    }
}
