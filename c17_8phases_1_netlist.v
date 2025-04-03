module top( clk_1 , clk_2 , clk_3 , clk_4 , clk_5 , clk_6 , clk_7 , clk_8 , N1 , N2 , N3 , N6 , N7 , N22 , N23 );

input N1 , N2 , N3 , N6 , N7 ;
output N22 , N23 ;
wire n6 , n7 , n8 , n9 , n10 , n11 , buf_N7_n10_1 , buf_n6_n9_1 , buf_n9_N22_1 , buf_n11_N23_1 , buf_splitterfromN2_n8_1 , buf_splitterfromN2_n10_1 , splitterfromN2 , splitterfromN3 , splitterfromn7 ;

PI_AQFP N1_( clk_1 , N1 );
PI_AQFP N2_( clk_1 , N2 );
PI_AQFP N3_( clk_1 , N3 );
PI_AQFP N6_( clk_1 , N6 );
PI_AQFP N7_( clk_1 , N7 );
and_AQFP n6_( clk_3 , N1 , splitterfromN3 , 0 , 0 , n6 );
and_AQFP n7_( clk_3 , splitterfromN3 , N6 , 0 , 0 , n7 );
and_AQFP n8_( clk_6 , buf_splitterfromN2_n8_1 , splitterfromn7 , 0 , 1 , n8 );
or_AQFP n9_( clk_7 , buf_n6_n9_1 , n8 , 0 , 0 , n9 );
or_AQFP n10_( clk_5 , buf_splitterfromN2_n10_1 , buf_N7_n10_1 , 0 , 0 , n10 );
and_AQFP n11_( clk_7 , splitterfromn7 , n10 , 1 , 0 , n11 );
PO_AQFP N22_( clk_2 , buf_n9_N22_1 , 0 , N22 );
PO_AQFP N23_( clk_2 , buf_n11_N23_1 , 0 , N23 );
buf_AQFP buf_N7_n10_1_( clk_3 , N7 , 0 , buf_N7_n10_1 );
buf_AQFP buf_n6_n9_1_( clk_5 , n6 , 0 , buf_n6_n9_1 );
buf_AQFP buf_n9_N22_1_( clk_1 , n9 , 0 , buf_n9_N22_1 );
buf_AQFP buf_n11_N23_1_( clk_1 , n11 , 0 , buf_n11_N23_1 );
buf_AQFP buf_splitterfromN2_n8_1_( clk_4 , splitterfromN2 , 0 , buf_splitterfromN2_n8_1 );
buf_AQFP buf_splitterfromN2_n10_1_( clk_4 , splitterfromN2 , 0 , buf_splitterfromN2_n10_1 );
splitter_AQFP splitterfromN2_( clk_2 , N2 , 0 , splitterfromN2 );
splitter_AQFP splitterfromN3_( clk_2 , N3 , 0 , splitterfromN3 );
splitter_AQFP splitterfromn7_( clk_5 , n7 , 0 , splitterfromn7 );

endmodule