// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

/// @title ERC20Approve - Race condition in approve/transferFrom (SWC-114)
/// @notice Changing allowance while spending is in mempool allows double-spend
contract ERC20Approve {
    mapping(address => uint256) public balances;
    mapping(address => mapping(address => uint256)) public allowed;

    uint256 public totalSupply;

    constructor() public {
        totalSupply = 1000000;
        balances[msg.sender] = totalSupply;
    }

    function balanceOf(address account) public view returns (uint256) {
        return balances[account];
    }

    /// @notice BAD: Race condition — spender can transferFrom old allowance
    /// before this tx mines, then spend new allowance too (double spend)
    function approve(address spender, uint256 value) public returns (bool) {
        allowed[msg.sender][spender] = value; // no increaseAllowance/decreaseAllowance
        return true;
    }

    function transferFrom(address from, address to, uint256 value) public returns (bool) {
        require(balances[from] >= value, "Insufficient balance");
        require(allowed[from][msg.sender] >= value, "Allowance exceeded");
        balances[from] -= value;
        balances[to] += value;
        allowed[from][msg.sender] -= value;
        return true;
    }

    function transfer(address to, uint256 value) public returns (bool) {
        require(balances[msg.sender] >= value, "Insufficient balance");
        balances[msg.sender] -= value;
        balances[to] += value;
        return true;
    }
}
