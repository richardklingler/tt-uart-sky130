// Tiny Tapeout tile (spike): GateLab's UART echo chip in a Tiny Tapeout tile. The UART on the demo board's RP2040
// pins (ui_in[3] = RX, uo_out[4] = TX), the byte count on the other seven outputs (bits 0-3 and 5-7 of the count).
`default_nettype none

module tt_um_gatelab_uart_echo (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);
    wire       tx;
    wire [7:0] count;

    uart_echo #(.CLK_HZ(50_000_000)) echo (
        .clk(clk), .rst_n(rst_n), .uart_rx(ui_in[3]), .uart_tx(tx), .count(count)
    );

    assign uo_out  = {count[6:4], tx, count[3:0]};
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

    wire _unused = &{ena, ui_in[7:4], ui_in[2:0], uio_in, count[7], 1'b0};
endmodule
