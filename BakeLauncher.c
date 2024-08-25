#include <stdio.h>
#include <unistd.h>
#include <direct.h>

int main() {
    // Switch to "main" folder
    if(chdir("main") != 0) {
        perror("Switch to BakeLauncher main folder failed");
        return 1;
    }

    // run main :)
    if (system("__main__.exe") != 0) {
        perror("Can't start BakeLauncher main!");
        perror("Maybe your BakeLauncher's file are corrpted :(");
        return 1;
    }
    return 0;
}