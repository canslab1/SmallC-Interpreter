/* Pointers - Pointer and dynamic memory example */

void swap(int *a, int *b) {
    int temp;
    temp = *a;
    *a = *b;
    *b = temp;
}

int main() {
    int x;
    int y;
    x = 10;
    y = 20;

    printf("Before swap: x=%d, y=%d\n", x, y);
    swap(&x, &y);
    printf("After swap: x=%d, y=%d\n", x, y);

    /* Dynamic memory */
    int *arr;
    arr = malloc(5 * 4);

    int i;
    for (i = 0; i < 5; i++) {
        *(arr + i) = i * i;
    }

    printf("Dynamic array: ");
    for (i = 0; i < 5; i++) {
        printf("%d ", *(arr + i));
    }
    printf("\n");

    free(arr);
    return 0;
}
