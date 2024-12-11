### Immediate Goals

1) Test Case 1 - adjsutments needed
        need to make second mult execute 1 cycle sooner on report timetable
        Its limited by FU not RS so we can start immediately after execution, not writeback like RS
        Our report is wrong, our code is right

        *Change Instruction 7 execution cycle from 27-46 to 26-45 and all the following instructions*
        *Change Final F4 value to 0*

2) Test Case 2 - adjustments needed
        do we wait until the entire store commit has finished before starting the next commit?
        We were pipelined them in the report and that seemed okay but Its not like that now for some reason
        The LD/SD code commits on the last cycle instead of the first so this would need to retroactively be changed since the ROB will block next instruction
        Can make it like report if we commit on first cycle instead of last and clear ROB but idk - I think this is okay - design choice...

        LD memory stage takes forver to occur but this okay since we have the load store queue setup so it is different than the project report

        *Change F1 final to 51.84*

3) Test Case 3 -



# Set up Inststruction

- pip install -r requirements.txt

# How to run

- python3 project.py
