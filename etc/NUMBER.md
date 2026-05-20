json_number:
(?x)
^
-?                                  # Optional negative sign
(?:
    0                               # Can be a lone zero
    |
    [1-9][0-9]* # Or a non-zero digit followed by any number of digits
)
(?: \. [0-9]+ )?                    # Optional fraction: dot MUST be followed by 1+ digits
(?: [eE] [+-]? [0-9]+ )?            # Optional exponent component
$


