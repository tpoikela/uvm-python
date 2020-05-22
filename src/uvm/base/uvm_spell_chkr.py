#
#------------------------------------------------------------------------------
#   Copyright 2011 Mentor Graphics Corporation
#   Copyright 2011 Cadence Design Systems, Inc.
#   Copyright 2011 Synopsys, Inc.
#   Copyright 2019 Tuomas Poikela
#   All Rights Reserved Worldwide
#
#   Licensed under the Apache License, Version 2.0 (the
#   "License"); you may not use this file except in
#   compliance with the License.  You may obtain a copy of
#   the License at
#
#       http:#www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in
#   writing, software distributed under the License is
#   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#   CONDITIONS OF ANY KIND, either express or implied.  See
#   the License for the specific language governing
#   permissions and limitations under the License.
#------------------------------------------------------------------------------

from typing import List
from ..macros.uvm_message_defines import uvm_info
from .uvm_object_globals import UVM_NONE


class UVMSpellChkr:

    max_val = 1

    #typedef T tab_t[string];
    #static const int unsigned max = '1;

    @classmethod
    def check(cls, strtab, s):
        """
        Primary interface to the spell checker.  The function takes two
        arguments, a table of strings and a string to check.  The table is
        organized as an associative array of type T.  E.g.

           T strtab[string]

        It does not matter what T is since we are only concerned with the
        string keys. However, we need T in order to make argument types
        match.

        First, we do the simple thing and see if the string already is in
        the string table by calling the ~exists()~ method.  If it does exist
        then there is a match and we're done.  If the string doesn't exist
        in the table then we invoke the spell checker algorithm to see if
        our string is a misspelled variation on a string that does exist in
        the table.

        The main loop traverses the string table computing the levenshtein
        distance between each string and the string we are checking.  The
        strings in the table with the minimum distance are considered
        possible alternatives.  There may be more than one string in the
        table with a minimum distance. So all the alternatives are stored
        in a queue.

        Note: This is not a particularly efficient algorithm.  It requires
        computing the levenshtein distance for every string in the string
        table.  If that list were very large the run time could be long.
        For the resources application in UVM probably the size of the
        string table is not excessive and run times will be fast enough.
        If, on average, that proves to be an invalid assumption then we'll
        have to find ways to optimize this algorithm.

        note: strtab should not be modified inside check()

        Args:
            strtab:
            s:
        Returns:
            bool: True if check matches, False otherwise
        """
        key = ""
        distance = 0
        min_val = 0
        min_key = []

        if s in strtab:
            return True

        min_val = UVMSpellChkr.max_val
        for key in strtab:
            distance = UVMSpellChkr.levenshtein_distance(key, s)

            # A distance < 0 means either key, s, or both are empty.  This
            # should never happen here but we check for that condition just
            # in case.
            if distance < 0:
                continue

            if distance < min_val:
                # set a new minimum.  Clean out the queue since previous
                # alternatives are now invalidated.
                min_val = distance
                min_key = []
                min_key.append(key)
                continue

            if distance == min_val:
                min_key.append(key)

        # if (min == max) then the string table is empty
        if min_val == UVMSpellChkr.max_val:
            uvm_info("UVM/CONFIGDB/SPELLCHK",
                "{} not located, no alternatives to suggest".format(s), UVM_NONE)
        else:
            # dump all the alternatives with the minimum distance
            q = []
            for i in range(0, len(min_key)):
                q.append(min_key[i])
                q.append("|")
                if len(q) > 0:
                    q.pop()
                    uvm_info("UVM/CONFIGDB/SPELLCHK",
                            "{} not located, did you mean {}".format(s,
                                "".join(q)),UVM_NONE)
        return False

    @classmethod
    def levenshtein_distance(cls, s, t) -> int:
        """
        levenshtein_distance

        Compute levenshtein distance between s and t
        The Levenshtein distance is defined as The smallest number of
        insertions, deletions, and substitutions required to change one
        string into another.  There is a tremendous amount of information
        available on Levenshtein distance on the internet.  Two good
        sources are wikipedia and nist.gov.  A nice, simple explanation of
        the algorithm is at
        http:#www.codeproject.com/KB/recipes/Levenshtein.aspx.  Use google
        to find others.

        This implementation of the Levenshtein
        distance computation algorithm is a SystemVerilog adaptation of the
        C implementatiion located at http:#www.merriampark.com/ldc.htm.

        Args:
            s:
            t:
        Returns:
        """
        k        = 0
        i        = 0
        j        = 0
        n        = 0
        m        = 0
        cost     = 0
        distance = 0
        d: List[int] = []

        #Step 1
        n = len(s) + 1
        m = len(t) + 1

        if n == 1 or m == 1:
            return -1  # negative return value means that one or both strings are empty.

        d = m*n * [0]

        #Step 2
        for k in range(0, n):
            d[k] = k

        for k in range(0, m):
            d[k*n] = k

        #Steps 3 and 4
        for i in range(1, n):
            for j in range(1, m):
                #Step 5
                cost = s[i-1] != t[j-1]

                #Step 6
                d[j*n+i] = UVMSpellChkr.minimum(d[(j-1)*n+i]+1, d[j*n+i-1]+1, d[(j-1)*n+i-1]+cost)

        distance = d[n*m-1]
        return distance

    @classmethod
    def minimum(cls, a: int, b: int, c: int) -> int:
        """
        Gets the minimum of three values

        Args:
            a (int):
            b (int):
            c (int):
        Returns:
            int: Minimum of given value.
        """
        return min(a, b, c)
