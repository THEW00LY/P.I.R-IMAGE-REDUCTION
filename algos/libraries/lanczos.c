/*
 *
 *  compiler une librair
 *  gcc -shared -O2 -o lanczos.dll lanczos.c <-- Windows
 *  gcc -dynamiclib -O2 -arch arm64 -arch x86_64 -o lanczos.dylib lanczos.c <-- MacOS et Linux (pas testé encore) -> compatible ARM et x86 (merci les puces M ...)
 *
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#ifdef _WIN32
  #define EXPORT __declspec(dllexport)
#else
  #define EXPORT
#endif

#define PI 3.141592

float lanczos_kernel(int x, int a)
{
    if(x == 0) return 1.0;
    if(abs(x) < a)
    {
        return (a * sin(PI * x) * sin(PI * x / a)) / (PI * PI * x * x);
    }
    return 0.0;
}

EXPORT int* lanczos(int *img, int old_h, int old_w, int new_h, int new_w, int a) {
    int* output = malloc(new_w * new_h * 3 * sizeof(int));

    float scale_w = (float)old_w / new_w;
    float scale_h = (float)old_h / new_h;

    for(int y = 0; y < new_h; y++)
    {
        for(int x = 0; x < new_w; x++)
        {
            int old_coordinates_x = (int)(x * scale_w);
            int old_coordinates_y = (int)(y * scale_h);

            float RGB_val[3] = {0.0f, 0.0f, 0.0f};
            float total_weight = 0.0f;

            int start_x = old_coordinates_x - a + 1;
            int start_y = old_coordinates_y - a + 1;
            int end_x   = old_coordinates_x + a + 1;
            int end_y   = old_coordinates_y + a + 1;

            for(int neighbor_y = start_y; neighbor_y < end_y; neighbor_y++)
            {
                for(int neighbor_x = start_x; neighbor_x < end_x; neighbor_x++)
                {
                    // Vérification bordures corrigée (>= au lieu de >)
                    if(neighbor_x < 0 || neighbor_x >= old_w || neighbor_y < 0 || neighbor_y >= old_h) continue;

                    int distance_x = old_coordinates_x - neighbor_x;
                    int distance_y = old_coordinates_y - neighbor_y;

                    float weight = lanczos_kernel(distance_x, a) * lanczos_kernel(distance_y, a);

                    // Indexation corrigée (neighbor_x au lieu de neighbor_y)
                    RGB_val[0] += img[neighbor_y * old_w * 3 + neighbor_x * 3 + 0] * weight;
                    RGB_val[1] += img[neighbor_y * old_w * 3 + neighbor_x * 3 + 1] * weight;
                    RGB_val[2] += img[neighbor_y * old_w * 3 + neighbor_x * 3 + 2] * weight;

                    total_weight += weight;
                }
            }

            if(total_weight == 0.0f)
            {
                output[y * new_w * 3 + x * 3 + 0] = 0;
                output[y * new_w * 3 + x * 3 + 1] = 0;
                output[y * new_w * 3 + x * 3 + 2] = 0;
            }
            else
            {
                output[y * new_w * 3 + x * 3 + 0] = (int)(RGB_val[0] / total_weight);
                output[y * new_w * 3 + x * 3 + 1] = (int)(RGB_val[1] / total_weight);
                output[y * new_w * 3 + x * 3 + 2] = (int)(RGB_val[2] / total_weight);
            }
        }
    }
    return output;
}