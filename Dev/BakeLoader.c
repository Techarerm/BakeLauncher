#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>

int main() {
    printf("BakeLauncher C Loader :)\n");
    printf("Version: 1.0.1\n");

    // run main :)
    if (system("python3 __main__.py") != 0) {
        perror("Can't start BakeLauncher main!");
        perror("Maybe your BakeLauncher's file are corrpted :(");
        return 1;
    }
    return 0;
}
