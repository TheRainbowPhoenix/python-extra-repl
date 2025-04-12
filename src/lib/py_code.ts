export const code = `
from gint import *
dclear(C_WHITE)
for y in range(DHEIGHT):
    for x in range(DWIDTH):
        if (x^y) & 1:
            dpixel(x, y, C_BLACK)
dupdate()

`;
