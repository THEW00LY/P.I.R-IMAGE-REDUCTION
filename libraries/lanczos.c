#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/*
 *
 *  compiler une librair
 *  gcc -shared -O2 -o lanczos.dll lanczos.c <-- Windows
 *  gcc -dynamiclib -O2 -arch arm64 -arch x86_64 -o lanczos.dylib lanczos.c <-- MacOS et Linux (pas testé encore) -> compatible ARM et x86 (merci les puces M ...)
 *
*/

// Made by GPT pour l'instant
// IMPORTANT : toutes les fonctions exposées à Python doivent être déclarées
// avec cette macro pour éviter le name-mangling C++
#ifdef _WIN32
  #define EXPORT __declspec(dllexport)
#else
  #define EXPORT
#endif

#define PI 3.141592

// Fonction algorithme lanczos
// Entrée : 
//  - img : Un pointeur vers un array 3D : weight, length, nb_composante
//  - new_h et new_w : nouvelles dimensions
//  - a : facteur de précision (plus grand -> mieux mais plus long)
// Sortie :
//  - Un pointeur vers un array 3D : weight, length, nb_composante

float lanczos_kernel(int x, int a)
{
  if(x == 0) return 1.0;
  
  if(abs(x) < a)
  {
    return (a*sin(PI*x)*sin(PI*x/a))/(PI*PI*x*x);
  }
  
  return 0.0;
}

// Pistes d'amélioration :
// - Pour l'instant ca marche uniquement pour RGB
// - Faire des pré-calculs pour les voisinage
EXPORT int* lanczos(int *img, int old_h, int old_w, int new_h, int new_w, int a) {

    int* output = malloc(new_w * 3 * new_h * 3 * sizeof(int)); // On prends en compte que chaque pixel est RGB.

    // Calcul des rapports
    // Rq : le calcul se faisant qu'une seule fois, on type en float pour avoir une bonne précision. Plus bas, on utilisera des int (arrondi inférieur)
    float scale_w = old_w / new_w;
    float scale_h = old_h / new_h;

    // On va balayer toute l'image (pour l'instant vide avec les nouvelles taille)
    for(int x = 0; x < new_h; x++)
    {
      for(int y = 0; y < new_w; y++)
      {

          // Récupérer les coordonnées associés à l'image de base
          int old_coordinates_x = x * scale_w;
          int old_coordinates_y = y * scale_h;

          int RGB_val[3] = {0, 0, 0};
          int total_weight = 0;

          // On regarde désormais les voisins avec un écart de a (merci gcc pour opistimiser tout ca ^^)
          int start_x = old_coordinates_x - a + 1;
          int start_y = old_coordinates_y - a + 1;
          int end_x = old_coordinates_x + a + 1;
          int end_y = old_coordinates_y + a + 1;
          
          for (int neighbor_y = start_y; neighbor_y < end_y; neighbor_y++)
          {
            for(int neighbor_x = start_x; neighbor_x < end_x; neighbor_x++)
            {

              // Vérification des bordures
              if(neighbor_x < 0 || neighbor_x > old_w || neighbor_y < 0 || neighbor_y > old_h) continue;

              int distance_x = old_coordinates_x - neighbor_x;
              int distance_y = old_coordinates_y - neighbor_y;

              int weight = lanczos_kernel(distance_x, a) * lanczos_kernel(distance_y, a);

              // On récupére les constantes RGB de l'image aux coordonnées x y z
              RGB_val[0] += img[neighbor_y * old_w * 3 + neighbor_x * 3 + 0] * weight;
              RGB_val[1] += img[neighbor_y * old_w * 3 + neighbor_x * 3 + 1] * weight;
              RGB_val[2] += img[neighbor_y * old_w * 3 + neighbor_x * 3 + 2] * weight;

              total_weight += weight;

            }
          }

          if(total_weight == 0)
          {
            output[x*new_w*3+y*3+0] = 0;
            output[x*new_w*3+y*3+1] = 0;
            output[x*new_w*3+y*3+2] = 0;
          }
          else
          {
            output[x*new_w*3+y*3+0] = RGB_val[0] / total_weight;
            output[x*new_w*3+y*3+1] = RGB_val[1] / total_weight;
            output[x*new_w*3+y*3+2] = RGB_val[2] / total_weight;
          }
      }

    }

    return output;

}