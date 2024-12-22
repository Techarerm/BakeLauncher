#include <stdio.h>
#include <stdlib.h>
#include <libgen.h>
#include <limits.h>
#include <string.h>

#ifdef _WIN32
    #include <windows.h>
    #include <direct.h>
    #define chdir _chdir   // Use _chdir on Windows
    #define GIT_CHECK "where git > NUL 2>&1"
#else
    #include <unistd.h> // Chdir...
    #define GIT_CHECK "which git > /dev/null 2>&1"
    #ifdef __APPLE__
        #include <mach-o/dyld.h>  // For _NSGetExecutablePath() on macOS
    #else
        #include <linux/limits.h>  // For PATH_MAX on Linux
    #endif
#endif

void run_python_script() {
    // Run the Python script
    if (system("python3 main.py") == -1) {
        perror("Error running Python script");
        exit(EXIT_FAILURE);
    }
}



void run_git_pull() {
    // Check if the git command exists
    if (system(GIT_CHECK) != 0) {
        perror("git command not found");
        run_python_script();  // If git is not found, only run the Python script
    } else {
        // Run git pull
        if (system("git pull") == -1) {
            perror("Error running git pull");
            exit(EXIT_FAILURE);
        }
        // Then run the Python script
        run_python_script();
    }
}


int main(int argc, char *argv[]) {
    printf("BakeLauncher C Loader :)\n");
    printf("You can run './BakeLoader -u' to update source code.\n");
    printf("Version: 1.0.2\n");

    char path[PATH_MAX];

    #ifdef _WIN32
        // Windows version
        if (GetModuleFileName(NULL, path, sizeof(path)) != 0) {
            char *dir = dirname(path);  // Extract the directory part
            printf("Executable is in: %s\n", dir);

            // Change working directory to the BakeLoader directory
            if (chdir(dir) == 0) {
                printf("Changed working directory to: %s\n", dir);
            } else {
                perror("Failed to change working directory into launcher source code path :(");
            }
        } else {
            fprintf(stderr, "Get main path failed.\n");
        }

    #elif __APPLE__
        // macOS version
        uint32_t size = sizeof(path);
        if (_NSGetExecutablePath(path, &size) == 0) {
            char *dir = dirname(path);  // Extract the directory part
            printf("Executable is in: %s\n", dir);

            // Change working directory to the executable's directory
            if (chdir(dir) == 0) {
                printf("Changed working directory to: %s\n", dir);
            } else {
                perror("Failed to change working directory into launcher source code path :(");
            }
        } else {
            fprintf(stderr, "Failed to get path. Cause by (Path too long. Please move main folder to other place).\n");
        }

    #else
        // Linux/Unix-specific code
        ssize_t len = readlink("/proc/self/exe", path, sizeof(path) - 1); // Linux-specific
        if (len != -1) {
            path[len] = '\0';  // Null-terminate the path
            char *dir = dirname(path);  // Extract the directory part
            printf("Executable is in: %s\n", dir);

            // Change working directory to the executable's directory
            if (chdir(dir) == 0) {
                printf("Changed working directory to: %s\n", dir);
            } else {
                perror("Failed to change working directory into launcher source code path :(");
            }
        } else {
            perror("Failed to get main path. Cause by readlink() error.");
        }
    #endif

    // Check for arguments
    if (argc > 1 && strcmp(argv[1], "-u") == 0) {
        run_git_pull();

        // After running git pull, execute main
        run_python_script();
    } else {
        run_python_script();
    }
    return 0;
}
