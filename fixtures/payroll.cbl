       IDENTIFICATION DIVISION.
       PROGRAM-ID. PAYROLL.
       AUTHOR. RETRO-TRANSFORMER.
      * Compute gross pay for three employees and total it.
       ENVIRONMENT DIVISION.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 PAY-RECORD.
           05 EMP-NAME      PIC X(20).
           05 EMP-HOURS     PIC 9(3)V99.
           05 EMP-RATE      PIC 9(4)V99.
           05 EMP-GROSS     PIC 9(6)V99.
       01 WS-COUNTERS.
           05 WS-I          PIC 9(3) VALUE 0.
           05 WS-TOTAL      PIC 9(8)V99 VALUE 0.
       PROCEDURE DIVISION.
       MAIN-LOGIC.
           PERFORM CALC-PAY 3 TIMES.
           DISPLAY 'TOTAL: ' WS-TOTAL.
           STOP RUN.
       CALC-PAY.
           ADD 1 TO WS-I.
           COMPUTE EMP-GROSS = EMP-HOURS * EMP-RATE.
           IF EMP-GROSS > 1000
               DISPLAY 'BIG CHECK'
           ELSE
               DISPLAY 'SMALL CHECK'
           END-IF.
           ADD EMP-GROSS TO WS-TOTAL.
