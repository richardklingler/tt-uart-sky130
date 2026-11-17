# SPDX-License-Identifier: Apache-2.0
# GateLab spike: the UART echo tile. 115200 baud 8N1 at a 50 MHz clock; RX on ui_in[3], TX on uo_out[4].

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, Timer

CLK_NS = 20
BIT_CLOCKS = round(50_000_000 / 115200)  # 434


async def send(dut, byte):
    """One 8N1 frame on ui_in[3], least significant bit first."""
    bits = [0] + [(byte >> i) & 1 for i in range(8)] + [1]
    for bit in bits:
        dut.ui_in.value = bit << 3
        await ClockCycles(dut.clk, BIT_CLOCKS)


async def receive(dut):
    """One 8N1 frame from uo_out[4], sampled in the middle of each bit."""
    for _ in range(40 * BIT_CLOCKS):
        await ClockCycles(dut.clk, 1)
        if not (int(dut.uo_out.value) >> 4) & 1:
            break
    else:
        assert False, "no start bit on uo_out[4]"
    await ClockCycles(dut.clk, BIT_CLOCKS // 2)
    assert not (int(dut.uo_out.value) >> 4) & 1, "start bit too short"
    value = 0
    for i in range(8):
        await ClockCycles(dut.clk, BIT_CLOCKS)
        value |= ((int(dut.uo_out.value) >> 4) & 1) << i
    await ClockCycles(dut.clk, BIT_CLOCKS)
    assert (int(dut.uo_out.value) >> 4) & 1, "no stop bit"
    return value


def count(dut):
    out = int(dut.uo_out.value)
    return (out & 0x0F) | ((out >> 5) << 4)


@cocotb.test()
async def test_echo(dut):
    cocotb.start_soon(Clock(dut.clk, CLK_NS, unit="ns").start())
    dut.ena.value = 1
    dut.ui_in.value = 1 << 3  # the line idles high
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 10)
    assert count(dut) == 0
    for n, byte in enumerate([0x4B, 0xD2], start=1):
        sender = cocotb.start_soon(send(dut, byte))
        echoed = await receive(dut)
        await sender
        assert echoed == byte, f"sent {byte:#04x}, got {echoed:#04x}"
        await ClockCycles(dut.clk, 2 * BIT_CLOCKS)
        assert count(dut) == n, f"count {count(dut)} after {n} bytes"
