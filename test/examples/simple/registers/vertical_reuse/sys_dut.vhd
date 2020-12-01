--
-- -------------------------------------------------------------
--    Copyright 2010 Mentor Graphics Corporation
--    Copyright 2004-2011 Synopsys, Inc.
--    Copyright 2019-2020 Tuomas Poikela (tpoikela)
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

entity sys_dut is
  generic (
    BASE_ADDR : natural := 16#100#;
    NUM_BLKS  : natural := 2);
  port (
    apb_pclk    : in  std_logic;
    apb_paddr   : in  unsigned(31 downto 0);
    apb_psel    : in  std_logic;
    apb_penable : in  std_logic;
    apb_pwrite  : in  std_logic;
    apb_prdata  : out std_logic_vector(31 downto 0);
    apb_pwdata  : in  std_logic_vector(31 downto 0);
    rst : in std_logic
    );
end sys_dut;

architecture structural of sys_dut is
begin

  b1 : entity work.blk_dut
    generic map (
      BASE_ADDR => BASE_ADDR)
    port map (
      apb_pclk    => apb_pclk,
      apb_paddr   => apb_paddr,
      apb_psel    => apb_psel,
      apb_penable => apb_penable,
      apb_pwrite  => apb_pwrite,
      apb_prdata  => apb_prdata,
      apb_pwdata  => apb_pwdata,
      rst         => rst);

  b2 : entity work.blk_dut
    generic map (
      BASE_ADDR => BASE_ADDR+16#100#)
    port map (
      apb_pclk    => apb_pclk,
      apb_paddr   => apb_paddr,
      apb_psel    => apb_psel,
      apb_penable => apb_penable,
      apb_pwrite  => apb_pwrite,
      apb_prdata  => apb_prdata,
      apb_pwdata  => apb_pwdata,
      rst         => rst);

end structural;
