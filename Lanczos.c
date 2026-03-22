#include <stdio.h>
#include <stdlib.h>
#include <jpeglib.h>
#define _USE_MATH_DEFINES
#include <math.h>

float sinc(float x) {
    if (x == 0.0) {
        return 1.0;
    }
    else {
        return (sin(M_PI * x) / (M_PI * x) );
    }
}

float kernel(float x, int a) {
    if (fabs(x) < (float) a) {
        return sinc(x) * sinc( x/ (float) a);
    }
    return 0.0;
}

unsigned char* lanczos_reduction(
    unsigned char* img,
    int W,
    int H,
    int channels,
    int newW,
    int newH,
    int a
) {

}

int main() {
    //open jpeg image with jpeg-lib-turbo
    FILE *file = fopen("monimage.jpg", "rb");

    if (!file) {
        printf("Impossible d'ouvrir l'image\n");
        return 1;
    }
    //struct we must declare
    struct jpeg_decompress_struct cinfo;
    struct jpeg_error_mgr jerr;

    cinfo.err = jpeg_std_error(&jerr);
    jpeg_create_decompress(&cinfo);

    jpeg_stdio_src(&cinfo, file);
    jpeg_read_header(&cinfo, TRUE);

    jpeg_start_decompress(&cinfo);

    printf("Largeur: %d\n", cinfo.output_width);
    printf("Hauteur: %d\n", cinfo.output_height);
    printf("Canaux: %d\n", cinfo.output_components);

    int row_stride = cinfo.output_width * cinfo.output_components;

    unsigned char *buffer = malloc(row_stride);

    int width = cinfo.output_width;
    int height = cinfo.output_height;
    int channels = cinfo.output_components;

    unsigned char *image = malloc(width * height * channels);

    int row_stride = width * channels;

    while (cinfo.output_scanline < height) {

        unsigned char *rowptr = image + cinfo.output_scanline * row_stride;

        jpeg_read_scanlines(&cinfo, &rowptr, 1);

        
    }

    jpeg_finish_decompress(&cinfo);

    jpeg_destroy_decompress(&cinfo);
    fclose(file);

    free(buffer);

    return 0;
}