--
-- -------------------------------------------------------------
--    Copyright 2004-2011 Synopsys, Inc.
--    Copyright 2010 Mentor Graphics Corporation
--    All Rights Reserved Worldwide
--
--    Licensed under the Apache License, Version 2.0 (the
--    "License"); you may not use this file except in
--    compliance with the License.  You may obtain a copy of
--    the License at
--
--        http://www.apache.org/licenses/LICENSE-2.0
--
--    Unless required by applicable law or agreed to in
--    writing, software distributed under the License is
--    distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
--    CONDITIONS OF ANY KIND, either express or implied.  See
--    the License for the specific language governing
--    permissions and limitations under the License.
-- -------------------------------------------------------------
--

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity dut is
  generic (
    BASE_ADDR : natural := 0);
  port (
    apb_pclk    : in  std_logic;
    apb_paddr   : in  unsigned(31 downto 0);
    apb_psel    : in  std_logic;
    apb_penable : in  std_logic;
    apb_pwrite  : in  std_logic;
    apb_prdata  : out std_logic_vector(31 downto 0);
    apb_pwdata  : in  std_logic_vector(31 downto 0);
    rst         : in  std_logic
    );

end dut;

architecture bhv of dut is
  type t_fifo is array (0 to 8) of std_logic_vector(31 downto 0);
  signal fifo : t_fifo;

  signal w_idx    : natural;
  signal r_idx    : natural;
  signal used     : natural;
  signal pr_data  : std_logic_vector(31 downto 0);
  signal pr_addr  : unsigned(31 downto 0);
  signal in_range : boolean;

begin

  process (apb_paddr)
  begin
    pr_addr  <= apb_paddr - BASE_ADDR;
    in_range <= false;
    if (apb_paddr - BASE_ADDR) < 16#100# then
      in_range <= true;
    end if;
  end process;

  process (apb_penable, apb_psel, apb_pwrite, in_range, pr_data)
  begin
    if (apb_psel = '1' and apb_penable = '1' and apb_pwrite = '0' and in_range) then
      apb_prdata <= pr_data;
    else
      apb_prdata <= (others => 'Z');
    end if;
  end process;

  process (apb_pclk, rst)
  begin
    if rst = '1' then
      for idx in fifo'range loop
        fifo(idx) <= (others => '0');
      end loop;  -- idx
      w_idx <= 0;
      r_idx <= 0;
      used  <= 0;
    elsif rising_edge(apb_pclk) then
      -- Wait for a SETUP+READ or ENABLE+WRITE cycle
      if (apb_psel = '1' and apb_penable = apb_pwrite and pr_addr = 0) then
        pr_data <= (others => '0');
        if apb_pwrite = '1' then
          if used /= 8 then
            -- report "Writing";
            fifo(w_idx) <= apb_pwdata;
            w_idx       <= w_idx + 1;
            used        <= used + 1;
          end if;
        else
          if used /= 0 then
            -- report "Reading";
            pr_data     <= fifo(r_idx);
            fifo(r_idx) <= (others => '0');  -- just for debug; not necessary
            r_idx       <= r_idx + 1;
            used        <= used - 1;
          end if;
        end if;
      end if;
    end if;
  end process;

end bhv;
