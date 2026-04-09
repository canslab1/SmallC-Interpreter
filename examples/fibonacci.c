/* Fibonacci - Loop and array example */

#define MAX 20

int main() {
    int fib[20];
    int i;

    fib[0] = 0;
    fib[1] = 1;

    for (i = 2; i < MAX; i++) {
        fib[i] = fib[i - 1] + fib[i - 2];
    }

    printf("Fibonacci sequence:\n");
    for (i = 0; i < MAX; i++) {
        printf("fib[%d] = %d\n", i, fib[i]);
    }

    return 0;
}
