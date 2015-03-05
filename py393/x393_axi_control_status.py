from __future__ import print_function
'''
# Copyright (C) 2015, Elphel.inc.
# Methods that mimic Verilog tasks used for simulation  
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

@author:     Andrey Filippov
@copyright:  2015 Elphel, Inc.
@license:    GPLv3.0+
@contact:    andrey@elphel.coml
@deffield    updated: Updated
'''
__author__ = "Andrey Filippov"
__copyright__ = "Copyright 2015, Elphel, Inc."
__license__ = "GPL"
__version__ = "3.0+"
__maintainer__ = "Andrey Filippov"
__email__ = "andrey@elphel.com"
__status__ = "Development"
#import sys
#import x393_mem
from import_verilog_parameters import VerilogParameters
from x393_mem import X393Mem
#MCNTRL_TEST01_CHN4_STATUS_CNTRL=0
def hx(obj):
    try:
        return "0x%x"%obj
    except:
        return str(obj)
'''
Simulate Verilog concatenation. Input list tuple of items, each being a pair of (value, width)
'''    
def concat(items):
    val=0
    width=0
    for vw in reversed(items):
        v=vw[0]
        if vw[1]==1:
            v=(0,1)[v] # So True/False will also work, not juet o/1
        val |= (v & ((1 << vw[1])-1))<<width
        width += vw[1]
    return (val,width)

def bits(val,field):
    try:
        high=field[0]
        low=field[1]
        if low > high:
            low,high=high,low
    except:
        low=field+0 # will be error if not a number
        high=low
    return (val >> low) & ((1 << (high-low+1))-1)    
        
class X393AxiControlStatus(object):
    DRY_MODE= True # True
    DEBUG_MODE=1
#    vpars=None
    x393_mem=None
    target_phase=0 # TODO: set!
    def __init__(self, debug_mode=1,dry_mode=True):
        self.DEBUG_MODE=debug_mode
        self.DRY_MODE=dry_mode
#        self.vpars=VerilogParameters()
        self.x393_mem=X393Mem(debug_mode,dry_mode)
#        print ("+++++++++++++++ self.__dict__ ++++++++++++++++++++++++++")
#        print (self.__dict__)
#        print ("+++++++++++++++ VerilogParameters.__dict__ ++++++++++++++++++++++++++")
#        print (VerilogParameters.__dict__)
#        self.__dict__.update(VerilogParameters.__dict__) # Add verilog parameters to the class namespace
        self.__dict__.update(VerilogParameters.__dict__["_VerilogParameters__shared_state"]) # Add verilog parameters to the class namespace
        
#        print ("+++++++++++++++ self.__dict__ ++++++++++++++++++++++++++")
#        print (self.__dict__)
        '''
        Maybe import parameters into the module, not class namespace to use directly, w/o self. ?
#        __dict__.update(VerilogParameters.__dict__) # Add verilog parameters to the class namespace
        '''
        
    def write_contol_register(self, reg_addr, data):
        self.x393_mem.axi_write_single_w(self.CONTROL_ADDR+reg_addr, data)
    def read_and_wait_status(self, address):
        return self.x393_mem.axi_read_addr_w(self.STATUS_ADDR + address )
    
    def wait_status_condition(self,
                              status_address,         # input [STATUS_DEPTH-1:0] status_address;
                              status_control_address, # input [29:0] status_control_address;
                              status_mode,            # input  [1:0] status_mode;
                              pattern,                # input [25:0] pattern;        // bits as in read registers
                              mask,                   # input [25:0] mask;           // which bits to compare
                              invert_match,           # input        invert_match;   // 0 - wait until match to pattern (all bits), 1 - wait until no match (any of bits differ)
                              wait_seq):              # input        wait_seq; // Wait for the correct sequence number, False assume correct
        match=False
        while not match:
            data=self.read_and_wait_status(status_address)
            if wait_seq:
                seq_num = ((data >> self.STATUS_SEQ_SHFT) ^ 0x20) & 0x30
                data=self.read_and_wait_status(status_address)
                while (((data >> self.STATUS_SEQ_SHFT) ^ seq_num) & 0x30) !=0:
                    data=self.read_and_wait_status(status_address)
                    if self.DRY_MODE: break
            match = (((data ^ pattern) & mask & 0x3ffffff)==0)
            if invert_match:
                match = not match
            if self.DRY_MODE: break
    def wait_phase_shifter_ready(self):
        data=self.read_and_wait_status(self.MCONTR_PHY_STATUS_REG_ADDR)
        while (((data & self.STATUS_PSHIFTER_RDY_MASK) == 0) or (((data ^ self.target_phase) & 0xff) != 0)):
            data=self.read_and_wait_status(self.MCONTR_PHY_STATUS_REG_ADDR)
            if self.DRY_MODE: break

    def read_all_status(self):
#        print (self.__dict__)
#        for name in self.__dict__:
#            print (name+": "+str(name=='MCONTR_PHY_STATUS_REG_ADDR'))
#        print (self.__dict__['MCONTR_PHY_STATUS_REG_ADDR'])
        print ("MCONTR_PHY_STATUS_REG_ADDR:          %s"%(hx(self.read_and_wait_status(self.MCONTR_PHY_STATUS_REG_ADDR))))
        print ("MCONTR_TOP_STATUS_REG_ADDR:          %s"%(hx(self.read_and_wait_status(self.MCONTR_TOP_STATUS_REG_ADDR))))
        print ("MCNTRL_PS_STATUS_REG_ADDR:           %s"%(hx(self.read_and_wait_status(self.MCNTRL_PS_STATUS_REG_ADDR))))
        print ("MCNTRL_SCANLINE_STATUS_REG_CHN1_ADDR:%s"%(hx(self.read_and_wait_status(self.MCNTRL_SCANLINE_STATUS_REG_CHN1_ADDR))))
        print ("MCNTRL_SCANLINE_STATUS_REG_CHN3_ADDR:%s"%(hx(self.read_and_wait_status(self.MCNTRL_SCANLINE_STATUS_REG_CHN3_ADDR))))
        print ("MCNTRL_TILED_STATUS_REG_CHN2_ADDR:   %s"%(hx(self.read_and_wait_status(self.MCNTRL_TILED_STATUS_REG_CHN2_ADDR))))
        print ("MCNTRL_TILED_STATUS_REG_CHN4_ADDR:   %s"%(hx(self.read_and_wait_status(self.MCNTRL_TILED_STATUS_REG_CHN4_ADDR))))
        print ("MCNTRL_TEST01_STATUS_REG_CHN1_ADDR:  %s"%(hx(self.read_and_wait_status(self.MCNTRL_TEST01_STATUS_REG_CHN1_ADDR))))
        print ("MCNTRL_TEST01_STATUS_REG_CHN2_ADDR:  %s"%(hx(self.read_and_wait_status(self.MCNTRL_TEST01_STATUS_REG_CHN2_ADDR))))
        print ("MCNTRL_TEST01_STATUS_REG_CHN3_ADDR:  %s"%(hx(self.read_and_wait_status(self.MCNTRL_TEST01_STATUS_REG_CHN3_ADDR))))
        print ("MCNTRL_TEST01_STATUS_REG_CHN4_ADDR:  %s"%(hx(self.read_and_wait_status(self.MCNTRL_TEST01_STATUS_REG_CHN4_ADDR))))

    def program_status(self,
                       base_addr,   # input [29:0] base_addr;
                       reg_addr,    # input  [7:0] reg_addr;
                       mode,        # input  [1:0] mode;
                       seq_number): # input  [5:0] seq_number;
        '''
 // mode bits:
 // 0 disable status generation,
 // 1 single status request,
 // 2 - auto status, keep specified seq number,
 // 3 - auto, inc sequence number
         '''
        self.write_contol_register(base_addr + reg_addr, ((mode & 3)<< 6) | (seq_number * 0x3f))


    def program_status_all( self,
                            mode,     # input [1:0] mode;
                            seq_num): # input [5:0] seq_num;
        self.program_status (self.MCONTR_PHY_16BIT_ADDR,     self.MCONTR_PHY_STATUS_CNTRL,        mode,seq_num)# //MCONTR_PHY_STATUS_REG_ADDR=          'h0,
        self.program_status (self.MCONTR_TOP_16BIT_ADDR,     self.MCONTR_TOP_16BIT_STATUS_CNTRL,  mode,seq_num)# //MCONTR_TOP_STATUS_REG_ADDR=          'h1,
        self.program_status (self.MCNTRL_PS_ADDR,            self.MCNTRL_PS_STATUS_CNTRL,         mode,seq_num)# //MCNTRL_PS_STATUS_REG_ADDR=           'h2,
        self.program_status (self.MCNTRL_SCANLINE_CHN1_ADDR, self.MCNTRL_SCANLINE_STATUS_CNTRL,   mode,seq_num)#; //MCNTRL_SCANLINE_STATUS_REG_CHN2_ADDR='h4,
        self.program_status (self.MCNTRL_SCANLINE_CHN3_ADDR, self.MCNTRL_SCANLINE_STATUS_CNTRL,   mode,seq_num)# //MCNTRL_SCANLINE_STATUS_REG_CHN3_ADDR='h5,
        self.program_status (self.MCNTRL_TILED_CHN2_ADDR,    self.MCNTRL_TILED_STATUS_CNTRL,      mode,seq_num)# //MCNTRL_TILED_STATUS_REG_CHN4_ADDR=   'h6,
        self.program_status (self.MCNTRL_TILED_CHN4_ADDR,    self.MCNTRL_TILED_STATUS_CNTRL,      mode,seq_num)#; //MCNTRL_TILED_STATUS_REG_CHN4_ADDR=   'h6,
        self.program_status (self.MCNTRL_TEST01_ADDR,        self.MCNTRL_TEST01_CHN1_STATUS_CNTRL,mode,seq_num)#; //MCNTRL_TEST01_STATUS_REG_CHN2_ADDR=  'h3c,
        self.program_status (self.MCNTRL_TEST01_ADDR,        self.MCNTRL_TEST01_CHN2_STATUS_CNTRL,mode,seq_num)#; //MCNTRL_TEST01_STATUS_REG_CHN2_ADDR=  'h3c,
        self.program_status (self.MCNTRL_TEST01_ADDR,        self.MCNTRL_TEST01_CHN3_STATUS_CNTRL,mode,seq_num)#; //MCNTRL_TEST01_STATUS_REG_CHN3_ADDR=  'h3d,
        self.program_status (self.MCNTRL_TEST01_ADDR,        self.MCNTRL_TEST01_CHN4_STATUS_CNTRL,mode,seq_num)#; //MCNTRL_TEST01_STATUS_REG_CHN4_ADDR=  'h3e,
        '''
        x393_tasks_ps_pio
        '''
    def schedule_ps_pio(self,          #; // shedule software-control memory operation (may need to check FIFO status first)
                        seq_addr,      # input [9:0] seq_addr; // sequence start address
                        page,          # input [1:0] page;     // buffer page number
                        urgent,        # input       urgent;   // high priority request (only for competion wityh other channels, wiil not pass in this FIFO)
                        chn,           # input       chn;      // channel buffer to use: 0 - memory read, 1 - memory write
                        wait_complete): # input       wait_complete; // Do not request a newe transaction from the scheduler until previous memory transaction is finished
        self.write_contol_register(self.MCNTRL_PS_ADDR + self.MCNTRL_PS_CMD,
                                    # {17'b0,
                                    ((0,1)[wait_complete]<<14) |
                                    ((0,1)[chn]<<13) |
                                    ((0,1)[urgent]<<12) |
                                    ((page & 3) << 10) |
                                    (seq_addr & 0x3ff))
 
    def wait_ps_pio_ready(self,      #; // wait PS PIO module can accept comamnds (fifo half empty)
                          mode,      # input [1:0] mode;
                          sync_seq): # input       sync_seq; //  synchronize sequences
        self.wait_status_condition (
            self.MCNTRL_PS_STATUS_REG_ADDR,
            self.MCNTRL_PS_ADDR + self.MCNTRL_PS_STATUS_CNTRL,
            mode & 3,
            0,
            2 << self.STATUS_2LSB_SHFT,
            0,
            sync_seq)

    def wait_ps_pio_done(self,      # // wait PS PIO module has no pending/running memory transaction
                         mode,      # input [1:0] mode;
                         sync_seq): # input       sync_seq; //  synchronize sequences
        self.wait_status_condition (
            self.MCNTRL_PS_STATUS_REG_ADDR,
            self.MCNTRL_PS_ADDR + self.MCNTRL_PS_STATUS_CNTRL,
            mode & 3,
            0,
            3 << self.STATUS_2LSB_SHFT,
            0,
            sync_seq)
    '''
    x393_mcontr_encode_cmd
    '''
    def func_encode_cmd(self,      # function [31:0] 
                        addr,      # input               [14:0] addr;       // 15-bit row/column adderss
                        bank,      # input                [2:0] bank;       // bank (here OK to be any)
                        rcw,       # input                [2:0] rcw;        // RAS/CAS/WE, positive logic
                        odt_en,    # input                      odt_en;     // enable ODT
                        cke,       # input                      cke;        // disable CKE
                        sel,       # input                      sel;        // first/second half-cycle, other will be nop (cke+odt applicable to both)
                        dq_en,     # input                      dq_en;      // enable (not tristate) DQ  lines (internal timing sequencer for 0->1 and 1->0)
                        dqs_en,    # input                      dqs_en;     // enable (not tristate) DQS lines (internal timing sequencer for 0->1 and 1->0)
                        dqs_toggle,# input                      dqs_toggle; // enable toggle DQS according to the pattern
                        dci,       # input                      dci;        // DCI disable, both DQ and DQS lines (internal logic and timing sequencer for 0->1 and 1->0)
                        buf_wr,    # input                      buf_wr;     // connect to external buffer (but only if not paused)
                        buf_rd,    # input                      buf_rd;     // connect to external buffer (but only if not paused)
                        nop,       # input                      nop;        // add NOP after the current command, keep other data
                        buf_rst):  # input                      buf_rst;    // connect to external buffer (but only if not paused)
        return (
            ((addr & 0x7fff) << 17) | # addr[14:0], // 15-bit row/column adderss
            ((bank & 0x7)    << 14) | # bank [2:0], // bank
            ((rcw  & 0x7)    << 11) | # rcw[2:0],   // RAS/CAS/WE
            ((0,1)[odt_en]   << 10) | # odt_en,     // enable ODT
            ((0,1)[cke]      <<  9) | # cke,        // may be optimized (removed from here)?
            ((0,1)[sel]      <<  8) | # sel,        // first/second half-cycle, other will be nop (cke+odt applicable to both)
            ((0,1)[dq_en]    <<  7) | # dq_en,      // enable (not tristate) DQ  lines (internal timing sequencer for 0->1 and 1->0)
            ((0,1)[dqs_en]   <<  6) | # dqs_en,     // enable (not tristate) DQS  lines (internal timing sequencer for 0->1 and 1->0)
            ((0,1)[dqs_toggle]<< 5) | # dqs_toggle, // enable toggle DQS according to the pattern
            ((0,1)[dci]      <<  4) | # dci,        // DCI disable, both DQ and DQS lines (internal logic and timing sequencer for 0->1 and 1->0)
            ((0,1)[buf_wr]   <<  3) | # buf_wr,     // phy_buf_wr,   // connect to external buffer (but only if not paused)
            ((0,1)[buf_rd]   <<  2) | # buf_rd,     // phy_buf_rd,    // connect to external buffer (but only if not paused)
            ((0,1)[nop]      <<  1) | # nop,        // add NOP after the current command, keep other data
            ((0,1)[buf_rst]  <<  0)   # buf_rst     // Reset buffer address/ increase buffer page
           )

    def func_encode_skip(self,       # function [31:0]
                          skip,       # input [CMD_PAUSE_BITS-1:0] skip;       // number of extra cycles to skip (and keep all the other outputs)
                          done,       # input                      done;       // end of sequence 
                          bank,       # input [2:0]                bank;       // bank (here OK to be any)
                          odt_en,     # input                      odt_en;     // enable ODT
                          cke,        # input                      cke;        // disable CKE
                          sel,        # input                      sel;        // first/second half-cycle, other will be nop (cke+odt applicable to both)
                          dq_en,      # input                      dq_en;      // enable (not tristate) DQ  lines (internal timing sequencer for 0->1 and 1->0)
                          dqs_en,     # input                      dqs_en;     // enable (not tristate) DQS lines (internal timing sequencer for 0->1 and 1->0)
                          dqs_toggle, # input                      dqs_toggle; // enable toggle DQS according to the pattern
                          dci,        # input                      dci;        // DCI disable, both DQ and DQS lines (internal logic and timing sequencer for 0->1 and 1->0)
                          buf_wr,     # input                      buf_wr;     // connect to external buffer (but only if not paused)
                          buf_rd,     # input                      buf_rd;     // connect to external buffer (but only if not paused)
                          buf_rst):   #input                      buf_rst;    // connect to external buffer (but only if not paused)
        return self.func_encode_cmd (
                ((0,1)[done] << self.CMD_PAUSE_BITS) |    # {{14-CMD_DONE_BIT{1'b0}}, done, 
                (skip & ((1 << self.CMD_PAUSE_BITS)-1)), # skip[CMD_PAUSE_BITS-1:0]},       // 15-bit row/column address
                bank & 7,   # bank[2:0],  // bank (here OK to be any)
                0,          # 3'b0,       // RAS/CAS/WE, positive logic
                odt_en,     #// enable ODT
                cke,        #// disable CKE
                sel,        #// first/second half-cycle, other will be nop (cke+odt applicable to both)
                dq_en,      #// enable (not tristate) DQ  lines (internal timing sequencer for 0->1 and 1->0)
                dqs_en,     #// enable (not tristate) DQS lines (internal timing sequencer for 0->1 and 1->0)
                dqs_toggle, #// enable toggle DQS according to the pattern
                dci,        #// DCI disable, both DQ and DQS lines (internal logic and timing sequencer for 0->1 and 1->0)
                buf_wr,     #// connect to external buffer (but only if not paused)
                buf_rd,     #// connect to external buffer (but only if not paused)
                0,          # 1'b0,       // nop
                buf_rst)    #
        
    def func_ddr3_mr0(self, # ; # function [ADDRESS_NUMBER+2:0]
                      pd, # input       pd; // precharge power down 0 - dll off (slow exit), 1 - dll on (fast exit) 
                      wr, # input [2:0] wr; // write recovery:
                          # 3'b000: 16
                          # 3'b001:  5
                          # 3'b010:  6
                          # 3'b011:  7
                          # 3'b100:  8
                          # 3'b101: 10
                          # 3'b110: 12
                          # 3'b111: 14
                      dll_rst,  # input       dll_rst; // 1 - dll reset (self clearing bit)
                      cl, # input [3:0] cl; // CAS latency (>=15ns):
                          # 0000: reserved                   
                          # 0010:  5                   
                          # 0100:  6                   
                          # 0110:  7                 
                          # 1000:  8                 
                          # 1010:  9                 
                          # 1100: 10                   
                          # 1110: 11                   
                          # 0001: 12                  
                          # 0011: 13                  
                          # 0101: 14
                      bt, #input       bt; # read burst type: 0 sequential (nibble), 1 - interleaved
                      bl):  #input [1:0] bl; # burst length:
        #                   2'b00 - fixed BL8
        #                   2'b01 - 4 or 8 on-the-fly by A12                                     
        #                   2'b10 - fixed BL4 (chop)
        #                   2'b11 - reserved
        return concat((
              (0,3),                      # 3'b0,
              (0,self.ADDRESS_NUMBER-13), #  {ADDRESS_NUMBER-13{1'b0}},
              (pd,1),              # pd,       # MR0.12 
              (wr,3),                     # wr,       # MR0.11_9
              (dll_rst,1),                # dll_rst,  # MR0.8
              (0,1),                      # 1'b0,     # MR0.7
              (cl>>1,3),                  # cl[3:1],  # MR0.6_4
              (bt,1),                     # bt,       # MR0.3
              (cl&1,1),                   # cl[0],    # MR0.2
              (bl,2)))[0]                 # bl[1:0]}; # MR0.1_0

    def func_ddr3_mr1(self, # function [ADDRESS_NUMBER+2:0] 
                      qoff, # input       qoff; # output enable: 0 - DQ, DQS operate in normal mode, 1 - DQ, DQS are disabled
                      tdqs, # input       tdqs; # termination data strobe (for x8 devices) 0 - disabled, 1 - enabled
                      rtt,  # input [2:0] rtt;  # on-die termination resistance:
                          #  3'b000 - disabled
                          #  3'b001 - RZQ/4 (60 Ohm)
                          #  3'b010 - RZQ/2 (120 Ohm)
                          #  3'b011 - RZQ/6 (40 Ohm)
                          #  3'b100 - RZQ/12(20 Ohm)
                          #  3'b101 - RZQ/8 (30 Ohm)
                          #  3'b11x - reserved
                      wlev, #input       wlev; # write leveling
                      ods, # input [1:0] ods;  # output drive strength:
                          #  2'b00 - RZQ/6 - 40 Ohm
                          #  2'b01 - RZQ/7 - 34 Ohm
                          #  2'b1x - reserved
                      al, # input [1:0] al;   # additive latency:
                          #  2'b00 - disabled (AL=0)
                          #  2'b01 - AL=CL-1;
                          #  2'b10 - AL=CL-2
                          #  2'b11 - reserved
                      dll): #input       dll;  # 0 - DLL enabled (normal), 1 - DLL disabled
        return concat (( #    ddr3_mr1 = {
              (1,3), # 3'h1,
              (0, self.ADDRESS_NUMBER-13), # {ADDRESS_NUMBER-13{1'b0}},
              (qoff,1),                    # qoff,       # MR1.12 
              (tdqs,1),                    # tdqs,       # MR1.11
              (0,1),                       # 1'b0,       # MR1.10
              (rtt>>2,1),                  # rtt[2],     # MR1.9
              (0,1),                       # 1'b0,       # MR1.8
              (wlev,1),                    # wlev,       # MR1.7 
              (rtt>>1,1),                  # rtt[1],     # MR1.6 
              (ods>>1,1),                  # ods[1],     # MR1.5 
              (al,2),                      # al[1:0],    # MR1.4_3 
              (rtt,1),                     # rtt[0],     # MR1.2 
              (ods,1),                     # ods[0],     # MR1.1 
              (dll)))[0]                   #dll};       # MR1.0 
    
        def func_ddr3_mr2(self, # ; function [ADDRESS_NUMBER+2:0] 
                          rtt_wr, # input [1:0] rtt_wr; # Dynamic ODT :
                            #  2'b00 - disabled
                            #  2'b01 - RZQ/4 = 60 Ohm
                            #  2'b10 - RZQ/2 = 120 Ohm
                            #  2'b11 - reserved
                            srt,  # input       srt;    # Self-refresh temperature 0 - normal (0-85C), 1 - extended (<=95C)
                            asr,  # input       asr;    # Auto self-refresh 0 - disabled (manual), 1 - enabled (auto)
                            cwl): # input [2:0] cwl;    # CAS write latency:
                            #  3'b000  5CK (           tCK >= 2.5ns)  
                            #  3'b001  6CK (1.875ns <= tCK < 2.5ns)  
                            #  3'b010  7CK (1.5ns   <= tCK < 1.875ns)  
                            #  3'b011  8CK (1.25ns  <= tCK < 1.5ns)  
                            #  3'b100  9CK (1.071ns <= tCK < 1.25ns)  
                            #  3'b101 10CK (0.938ns <= tCK < 1.071ns)  
                            #  3'b11x reserved
            return concat ((                  
                (2,3),                       #   3'h2,
                (0, self.ADDRESS_NUMBER-11), # {ADDRESS_NUMBER-11{1'b0}},
                (rtt_wr,2),                  # rtt_wr[1:0], # MR2.10_9
                (0,1),                       # 1'b0,        # MR2.8
                (srt,1),                     # srt,         # MR2.7
                (asr,1),                     # asr,         # MR2.6
                (cwl,3),                     # cwl[2:0],    # MR2.5_3
                (0,3)))[0]                   # 3'b0};       # MR2.2_0 

    def func_ddr3_mr3(self,       # function [ADDRESS_NUMBER+2:0]
                      mpr,        # input       mpr;    # MPR mode: 0 - normal, 1 - dataflow from MPR
                      mpr_rf):    # input [1:0] mpr_rf; # MPR read function:
                            #  2'b00: predefined pattern 0101...
                            #  2'b1x, 2'bx1 - reserved
        return concat((
                (3,3),                   # 3'h3,
                (0,self.ADDRESS_NUMBER), # {ADDRESS_NUMBER-3{1'b0}},
                (mpr, 1),                # mpr,          # MR3.2
                (mpr_rf,2)))[0]          # mpr_rf[1:0]}; # MR3.1_0 
        
    '''
    x393_tasks_pio_sequences
    '''
    def enable_reset_ps_pio(self, #; // control reset and enable of the PS PIO channel;
                            en,   # input en;
                            rst): #input rst;
        self.write_contol_register(self.MCNTRL_PS_ADDR + self.MCNTRL_PS_EN_RST,
                                   ((0,1)[en]<<1) | #{30'b0,en,
                                   (1,0)[rst])  #~rst});
   
   
    def set_read_block(self, #
                       ba,   # input [ 2:0] ba;
                       ra,   # input [14:0] ra;
                       ca):  #input [ 9:0] ca;
        cmd_addr = self.MCONTR_CMD_WR_ADDR + self.READ_BLOCK_OFFSET
# activate
        #                           addr                bank     RCW ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD NOP, B_RST
        data=self.func_encode_cmd(  ra,                  ba,      4,  0,  0,  0,  0,    0,    0,    0,  0,   0,   0,   0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# see if pause is needed . See when buffer read should be started - maybe before WR command
        #                          skip     done        bank         ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip( 1,       0,          0,           0,  0,  0,  0,    0,    0,    0,  0,   0,        0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr+=1
# first read
# read
        #                          addr                 bank     RCW ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD NOP, B_RST
        data=self.func_encode_cmd(ca&0x3ff,              ba,      2,  0,  0,  1,  0,    0,    0,    1,  1,   0,   0,   0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# nop
        #                          skip     done        bank         ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip( 0,       0,          ba,          0,  0,  1,  0,    0,    0,    1,  1,   0,        0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
#repeat remaining reads             
        for i in range(1,64):
# read
#                                  addr                 bank     RCW ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD NOP, B_RST
            data=self.func_encode_cmd((ca & 0x3ff)+(i<<3),ba,     2,  0,  0,  1,  0,    0,    0,    1,  1,   0,   1,   0)
            self.axi_write_single_w(cmd_addr, data)
            cmd_addr += 1
# nop - all 3 below are the same? - just repeat?
        #                          skip     done        bank         ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip(  0,       0,         ba,          0,  0,  1,  0,    0,    0,    1,  0,   0,        0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# nop
        #                          skip     done        bank         ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip(  0,       0,         ba,          0,  0,  1,  0,    0,    0,    1,  0,   0,        0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# nop
        #                          skip     done        bank         ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip(  0,       0,         ba,          0,  0,  1,  0,    0,    0,    1,  0,   0,        0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# tRTP = 4*tCK is already satisfied, no skip here
# precharge, end of a page (B_RST)         
        #                          addr                 bank     RCW ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD NOP, B_RST
        data=self.func_encode_cmd(  ra,                  ba,      5,  0,  0,  0,  0,    0,    0,    1,  0,   0,   0,   1)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
        #                          skip     done        bank         ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip(  2,       0,         0,           0,  0,  0,  0,    0,    0,    1,  0,   0,        0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# Turn off DCI, set DONE
        #                          skip     done        bank         ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip(  0,       1,         0,           0,  0,  0,  0,    0,    0,    0,  0,   0,        0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1

    def set_write_block(self, #):
                        ba,  # input[2:0]ba;
                        ra,  # input[14:0]ra;
                        ca): # input[9:0]ca;
        cmd_addr = self.MCONTR_CMD_WR_ADDR + self.WRITE_BLOCK_OFFSET
# activate
        #                          addr                 bank     RCW ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD NOP, B_RST
        data=self.func_encode_cmd( ra,                   ba,      4,  0,  0,  0,  0,    0,    0,    0,  0,   1,   0,   0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# see if pause is needed . See when buffer read should be started - maybe before WR command
        #                          skip     done        bank         ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip( 1,       0,          0,           0,  0,  0,  0,    0,    0,    0,  0,   1,        0) # tRCD - 2 read bufs
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# first write, 3 rd_buf
# write
        #                          addr                 bank     RCW ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD NOP, B_RST
        data=self.func_encode_cmd(ca&0x3ff,              ba,      3,  1,  0,  1,  0,    0,    0,    0,  0,   1,   0,   0) # B_RD moved 1 cycle earlier 
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# nop 4-th rd_buf
        #                          skip     done        bank         ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip( 0,       0,          ba,          1,  0,  0,  1,    1,    0,    0,  0,   1,        0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
#repeat remaining writes
        for i in range(1,62) : #(i = 1; i < 62; i = i + 1) begin
# write
        #                          addr                 bank     RCW ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD NOP, B_RST
            data=self.func_encode_cmd((ca&0x3ff)+(i<<3), ba,      3,  1,  0,  1,  1,    1,    1,    0,  0,   1,   1,   0) 
            self.axi_write_single_w(cmd_addr, data)
            cmd_addr += 1
        #                          addr                 bank     RCW ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD NOP, B_RST
        data=self.func_encode_cmd((ca&0x3ff)+(62<<3),    ba,      3,  1,  0,  1,  1,    1,    1,    0,  0,   1,   0,   0) # write w/o nop
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
#nop
        #                          skip     done        bank         ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip( 0,       0,          ba,          1,  0,  1,  1,    1,    1,    0,  0,   0,        0) # nop with buffer read off
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
        
# One last write pair w/o buffer
        #                          addr                 bank     RCW ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD NOP, B_RST
        data=self.func_encode_cmd((ca&0x3ff)+(63<<3),    ba,      3,  1,  0,  1,  1,    1,    1,    0,  0,   0,   1,   0) # write with nop
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# nop
        #                          skip     done        bank         ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip( 0,       0,          ba,          1,  0,  0,  1,    1,    1,    0,  0,   0,        0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# nop
        #                          skip     done        bank         ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip( 0,       0,          ba,          1,  0,  0,  1,    1,    1,    0,  0,   0,        1) # removed B_RD 1 cycle earlier
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# nop
        #                          skip     done        bank         ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip( 0,       0,          ba,          1,  0,  0,  1,    1,    1,    0,  0,   0,        0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# ODT off, it has latency
        #                          skip     done        bank         ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip( 2,       0,          ba,          0,  0,  0,  0,    0,    0,    0,  0,   0,        0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# precharge, ODT off
        #                          addr                 bank     RCW ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD NOP, B_RST
        data=self.func_encode_cmd(  ra,                  ba,      5,  0,  0,  0,  0,    0,    0,    0,  0,   0,   0,   0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
        #                          skip     done        bank         ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip( 2,       0,          ba,          0,  0,  0,  0,    0,    0,    0,  0,   0,        0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# Finalize, set DONE        
        #                          skip     done        bank         ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip( 0,       1,          0,           0,  0,  0,  0,    0,    0,    0,  0,   0,        0);
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1

# Set MR3, read nrep*8 words, save to buffer (port0). No ACTIVATE/PRECHARGE are needed/allowed   
    def set_read_pattern (self, 
                          nrep): # input integer nrep;
        cmd_addr = self.MCONTR_CMD_WR_ADDR + self.READ_PATTERN_OFFSET
        mr3_norm = self.func_ddr3_mr3(
           0, # 1'h0,     //       mpr;    // MPR mode: 0 - normal, 1 - dataflow from MPR
           0) # 2'h0);    // [1:0] mpr_rf; // MPR read function: 2'b00: predefined pattern 0101...
        mr3_patt = self.func_ddr3_mr3(
           1, # 1'h1,     //       mpr;    // MPR mode: 0 - normal, 1 - dataflow from MPR
           0) # 2'h0);    // [1:0] mpr_rf; // MPR read function: 2'b00: predefined pattern 0101...
# Set pattern mode
        #                           addr                 bank                   RCW ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD NOP, B_RST
        data=self.func_encode_cmd(bits(mr3_patt,(14,0)), bits(mr3_patt,(17,15)), 7,  0,  0,  0,  0,    0,    0,    0,  0,   0,   0,   0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
        #                          skip      done        bank                       ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data.self.func_encode_skip( 5,        0,           0,                         0,  0,  0,  0,    0,    0,    0,  0,   0,        0)# tMOD
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# first read
#@ read
        #                           addr                 bank                   RCW ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD NOP, B_RST
        data=self.func_encode_cmd(    0,                   0,                    2,  0,  0,  1,  0,    0,    0,    1,  1,   0,   0,   0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# nop (combine with previous?)
        #                          skip      done        bank                       ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip(   0,       0,          0,                        0,  0,  1,  0,    0,    0,    1,  1,   0,        0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
#repeat remaining reads
#        for (i = 1; i < nrep; i = i + 1) begin
        for _ in range(1,nrep):
        #                           addr                 bank                   RCW ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD NOP, B_RST
            data=self.func_encode_cmd( 0,                  0,                    2,  0,  0,  1,  0,    0,    0,    1,  1,   0,   1,   0)
            self.axi_write_single_w(cmd_addr, data)
            cmd_addr += 1
# nop - all 3 below are the same? - just repeat?
        #                          skip      done        bank                       ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip(   0,       0,          0,                        0,  0,  1,  0,    0,    0,    1,  1,   0,        0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# nop
        #                          skip      done        bank                       ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip(   0,       0,          0,                        0,  0,  1,  0,    0,    0,    1,  0,   0,        0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# nop
        #                          skip      done        bank                       ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip(   0,       0,          0,                        0,  0,  1,  0,    0,    0,    1,  0,   0,        0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# nop, no write buffer - next page
        #                          skip      done        bank                       ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip(   0,       0,          0,                        0,  0,  1,  0,    0,    0,    1,  0,   0,        1)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
        #                          skip      done        bank                       ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip(   1,       0,          0,                        0,  0,  1,  0,    0,    0,    1,  0,   0,        0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# Turn off read pattern mode
        #                           addr                 bank                   RCW ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD NOP, B_RST
        data=self.func_encode_cmd(bits(mr3_norm,(14,0)), bits(mr3_norm,(17,15)), 7,  0,  0,  0,  0,    0,    0,    1,  0,   0,   0,   0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# tMOD (keep DCI enabled)
        #                          skip      done        bank                       ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip(   5,       0,          0,                        0,  0,  0,  0,    0,    0,    1,  0,   0,        0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# Turn off DCI
        #                          skip      done        bank                       ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip(   0,       0,          0,                        0,  0,  0,  0,    0,    0,    0,  0,   0,        0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1
# Finalize (set DONE)
        #                          skip      done        bank                       ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data=self.func_encode_skip(   0,       1,          0,                        0,  0,  0,  0,    0,    0,    0,  0,   0,        0)
        self.axi_write_single_w(cmd_addr, data)
        cmd_addr += 1

        '''
task set_write_lev;
    input[CMD_PAUSE_BITS-1:0]nrep;
    reg[17:0] mr1_norm;
    reg[17:0] mr1_wlev;
    reg[29:0] cmd_addr;
    reg[31:0] data;
    reg[CMD_PAUSE_BITS-1:0] dqs_low_rpt;
    reg[CMD_PAUSE_BITS-1:0] nrep_minus_1;
    begin
        dqs_low_rpt <= 8;
        nrep_minus_1 <= nrep - 1;
        mr1_norm <= ddr3_mr1(
            1'h0,     //       qoff; // output enable: 0 - DQ, DQS operate in normal mode, 1 - DQ, DQS are disabled
            1'h0,     //       tdqs; // termination data strobe (for x8 devices) 0 - disabled, 1 - enabled
            3'h2,     // [2:0] rtt;  // on-die termination resistance: //  3'b010 - RZQ/2 (120 Ohm)
            1'h0,     //       wlev; // write leveling
            2'h0,     //       ods;  // output drive strength: //  2'b00 - RZQ/6 - 40 Ohm
            2'h0,     // [1:0] al;   // additive latency: 2'b00 - disabled (AL=0)
            1'b0);    //       dll;  // 0 - DLL enabled (normal), 1 - DLL disabled
        mr1_wlev <= ddr3_mr1(
            1'h0,     //       qoff; // output enable: 0 - DQ, DQS operate in normal mode, 1 - DQ, DQS are disabled
            1'h0,     //       tdqs; // termination data strobe (for x8 devices) 0 - disabled, 1 - enabled
            3'h2,     // [2:0] rtt;  // on-die termination resistance: //  3'b010 - RZQ/2 (120 Ohm)
            1'h1,     //       wlev; // write leveling
            2'h0,     //       ods;  // output drive strength: //  2'b00 - RZQ/6 - 40 Ohm
            2'h0,     // [1:0] al;   // additive latency: 2'b00 - disabled (AL=0)
            1'b0);    //       dll;  // 0 - DLL enabled (normal), 1 - DLL disabled
        cmd_addr <= MCONTR_CMD_WR_ADDR + WRITELEV_OFFSET;
// Enter write leveling mode
        @(posedge CLK)
        //                          addr                 bank     RCW ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD NOP, B_RST
        data <=  func_encode_cmd(mr1_wlev[14:0],  mr1_wlev[17:15], 7,  0,  0,  0,  0,    0,    0,    0,  0,   0,   0,   0);
        @(posedge CLK) axi_write_single_w(cmd_addr, data); cmd_addr <= cmd_addr + 1;
        //                          skip     done        bank         ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data <=  func_encode_skip(  13,       0,           0,          0,  0,  0,  0,    0,    0,    0,  0,   0,        0); // tWLDQSEN=25tCK
        @(posedge CLK) axi_write_single_w(cmd_addr, data); cmd_addr <= cmd_addr + 1;
// enable DQS output, keep it low (15 more tCK for the total of 40 tCK
        //                          skip     done        bank         ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data <=  func_encode_skip(dqs_low_rpt, 0,         0,           1,  0,  0,  0,    1,    0,    0,  0,   0,        0);
        @(posedge CLK) axi_write_single_w(cmd_addr, data); cmd_addr <= cmd_addr + 1;
// Toggle DQS as needed for write leveling, write to buffer
        //                          skip     done        bank         ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data <=  func_encode_skip(nrep_minus_1,0,         0,           1,  0,  0,  0,    1,    1,    1,  1,   0,        0);
        @(posedge CLK) axi_write_single_w(cmd_addr, data); cmd_addr <= cmd_addr + 1;
// continue toggling (5 times), but disable writing to buffer (used same wbuf latency as for read) 
        //                          skip     done        bank         ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data <=  func_encode_skip(  4,        0,         0,            1,  0,  0,  0,    1,    1,    1,  0,   0,        0);
        @(posedge CLK) axi_write_single_w(cmd_addr, data); cmd_addr <= cmd_addr + 1;
        // Keep DCI (but not ODT) active  ODT should be off befor MRS
        //                          skip     done        bank         ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data <=  func_encode_skip(  2,        0,         0,            0,  0,  0,  0,    0,    0,    1,  0,   0,        0);
        @(posedge CLK) axi_write_single_w(cmd_addr, data); cmd_addr <= cmd_addr + 1;
        // exit write leveling mode, ODT off, DCI off
        //                          addr                 bank     RCW ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD NOP, B_RST
        data <=  func_encode_cmd(mr1_norm[14:0],  mr1_norm[17:15], 7,  0,  0,  0,  0,    0,    0,    0,  0,   0,   0,   0);
        @(posedge CLK) axi_write_single_w(cmd_addr, data); cmd_addr <= cmd_addr + 1;
        //                          skip     done        bank         ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data <=  func_encode_skip(  5,        0,         0,            0,  0,  0,  0,    0,    0,    0,  0,   0,        0); // tMOD
        @(posedge CLK) axi_write_single_w(cmd_addr, data); cmd_addr <= cmd_addr + 1;
        // Finalize. See if DONE can be combined with B_RST, if not - insert earlier
        //                          skip     done        bank         ODT CKE SEL DQEN DQSEN DQSTGL DCI B_WR B_RD      B_RST
        data <=  func_encode_skip(   0,       1,           0,          0,  0,  0,  0,    0,    0,    0,  0,   0,        1); // can DONE be combined with B_RST?
        @(posedge CLK) axi_write_single_w(cmd_addr, data); cmd_addr <= cmd_addr + 1;
    end
endtask

        '''
        
    '''

        
   vpars1=VerilogParameters()
    print("vpars1.VERBOSE="+str(vpars1.VERBOSE))
    print("vpars1.VERBOSE__TYPE="+str(vpars1.VERBOSE__TYPE))
    print("vpars1.VERBOSE__RAW="+str(vpars1.VERBOSE__RAW))
        '''