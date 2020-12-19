library ieee;
use ieee.std_logic_1164.all;

entity common_stub is
  port (
    signal clk : in std_ulogic;
    signal rst : in std_ulogic);
end common_stub;

architecture bhv of common_stub is
  signal word : natural;
begin

  process (clk, rst) begin
    if rst = '0' then
      word <= 0;
    elsif rising_edge(clk) then
      word <= word + 1;
    end if;
  end process;

end bhv;
