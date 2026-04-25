// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

/// @title BECToken - Simplified BatchOverflow (CVE-2018-10299 pattern)
/// @notice Multiplying unchecked uint256 values causes overflow, minting free tokens
contract BECToken {
    string public name = "BeautyChain";
    string public symbol = "BEC";
    uint8 public decimals = 18;
    uint256 public totalSupply;
    mapping(address => uint256) public balances;
    
    address public owner;

    constructor() public {
        totalSupply = 7 * 10**27;
        owner = msg.sender;
        balances[msg.sender] = totalSupply;
    }

    function balanceOf(address account) public view returns (uint256) {
        return balances[account];
    }

    /// @notice BAD: no overflow check — cnt * value can overflow to small/zero
    function batchTransfer(address[] receivers, uint256 value) public returns (bool) {
        uint cnt = receivers.length;
        uint256 amount = uint256(cnt) * value; // OVERFLOW if cnt and value are large

        require(cnt > 0 && cnt <= 20, "Bad count");
        require(value > 0 && balances[msg.sender] >= amount, "Insufficient balance");

        balances[msg.sender] -= amount;
        for (uint i = 0; i < cnt; i++) {
            balances[receivers[i]] += value;
        }
        return true;
    }
}
