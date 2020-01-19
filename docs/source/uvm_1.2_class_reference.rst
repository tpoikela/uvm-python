uvm-python Class Reference
##########################

..
  See also https://verificationacademy.com/verification-methodology-reference/uvm/docs_1.2/html/index.html

.. toctree::

..
   overviews/intro
   overviews/relnotes

Base
====
.. toctree::

   overviews/base
   base/uvm_misc
   base/uvm_object
   base/uvm_transaction
   base/uvm_root
   base/uvm_port_base

Reporting
=========
.. toctree::

   overviews/reporting
   base/uvm_report_message
   base/uvm_report_object
   base/uvm_report_handler
   base/uvm_report_server
   base/uvm_report_catcher

Recording
=========
.. toctree::

   overviews/recording
   base/uvm_tr_database
   base/uvm_tr_stream

Factory
=======
.. toctree::

   overviews/factory
   base/uvm_registry
   base/uvm_factory

Phasing
=======
.. toctree::

   overviews/phasing
   base/uvm_phase
   base/uvm_domain
   base/uvm_bottomup_phase
   base/uvm_task_phase
   base/uvm_topdown_phase
   base/uvm_common_phases
   base/uvm_runtime_phases
   overviews/test_phasing

Configuration and Resources
===========================
.. toctree::

   overviews/config_and_res
   base/uvm_resource
   base/uvm_resource_db
   base/uvm_config_db

Synchronization
===============
.. toctree::

   overviews/synchro
   base/uvm_event
   base/uvm_event_callback
   base/uvm_barrier
   base/uvm_objection
   base/uvm_heartbeat
   base/uvm_callback

Containers
==========
.. toctree::

   overviews/containers
   base/uvm_pool
   base/uvm_queue

TLM
===
.. toctree::

   overviews/tlm_ifs_and_ports

TLM1
----
.. toctree::

   overviews/tlm1
   tlm1/uvm_tlm_ifs
   tlm1/uvm_ports
   tlm1/uvm_exports
   tlm1/uvm_imps
   tlm1/uvm_tlm_fifos
   tlm1/uvm_tlm_fifo_base
   tlm1/uvm_tlm_req_rsp
   tlm1/uvm_sqr_connections
   tlm1/uvm_sqr_ifs

TLM2
----
.. toctree::

   overviews/tlm2
   tlm2/uvm_tlm2_defines
   tlm2/uvm_tlm2_ifs
   tlm2/uvm_tlm2_generic_payload
   tlm2/uvm_tlm2_sockets_base
   tlm2/uvm_tlm2_sockets
   tlm2/uvm_tlm2_exports
   tlm2/uvm_tlm2_imps
   tlm2/uvm_tlm2_ports
   tlm2/uvm_tlm2_time
   tlm1/uvm_analysis_port

Components
==========
.. toctree::

   overviews/components
   base/uvm_component
   comps/uvm_test
   comps/uvm_env
   comps/uvm_agent
   comps/uvm_monitor
   comps/uvm_scoreboard
   comps/uvm_driver
   comps/uvm_push_driver
   comps/uvm_random_stimulus
   comps/uvm_subscriber

Comparators
-----------
.. toctree::

   overviews/comparators
   comps/uvm_in_order_comparator
   comps/uvm_algorithmic_comparator
   comps/uvm_pair
   comps/uvm_policies

Sequencers
==========
.. toctree::

   overviews/sequencers
   seq/uvm_sequencer_base
   seq/uvm_sequencer_param_base
   seq/uvm_sequencer
   seq/uvm_push_sequencer

Sequences
=========
.. toctree::

   overviews/sequences
   seq/uvm_sequence_item
   seq/uvm_sequence_base
   seq/uvm_sequence
   seq/uvm_sequence_library

Macros
======
.. toctree::

   overviews/macros
   macros/uvm_message_defines
   macros/uvm_global_defines
   macros/uvm_object_defines
   macros/uvm_sequence_defines
   macros/uvm_callback_defines
   macros/uvm_tlm_defines
   macros/uvm_reg_defines
   macros/uvm_version_defines

Policies
========
.. toctree::

   overviews/policies
   base/uvm_printer
   base/uvm_comparer
   base/uvm_recorder
   base/uvm_packer
   base/uvm_links

Data Access
-----------
.. toctree::

   overviews/dap
   dap/uvm_set_get_dap_base
   dap/uvm_simple_lock_dap
   dap/uvm_get_to_lock_dap
   dap/uvm_set_before_get_dap

Register Layer
==============
.. toctree::

   overviews/registers
   reg/uvm_reg_model

Register Model
--------------
.. toctree::

   reg/uvm_reg_block
   reg/uvm_reg_map
   reg/uvm_reg_file
   reg/uvm_reg
   reg/uvm_reg_field
   reg/uvm_mem
   reg/uvm_reg_indirect
   reg/uvm_reg_fifo
   reg/uvm_vreg
   reg/uvm_vreg_field
   reg/uvm_reg_cbs
   reg/uvm_mem_mam

DUT Integration
---------------
.. toctree::

   reg/uvm_reg_item
   reg/uvm_reg_adapter
   reg/uvm_reg_predictor
   reg/uvm_reg_sequence
   reg/uvm_reg_backdoor
   dpi/uvm_hdl

Test Sequences
--------------
.. toctree::

   reg/sequences/uvm_reg_mem_built_in_seq
   reg/sequences/uvm_reg_hw_reset_seq
   reg/sequences/uvm_reg_bit_bash_seq
   reg/sequences/uvm_reg_access_seq
   reg/sequences/uvm_reg_mem_shared_access_seq
   reg/sequences/uvm_mem_access_seq
   reg/sequences/uvm_mem_walk_seq
   reg/sequences/uvm_reg_mem_hdl_paths_seq

Command Line Processor
======================
.. toctree::

   overviews/cmdlineproc
   base/uvm_cmdline_processor

Globals
=======
.. toctree::

   overviews/globals
   base/uvm_object_globals
   base/uvm_globals
   base/uvm_coreservice
   base/uvm_traversal
