"""La caméra regarde la table : elle repère les 4 marqueurs, puis donne la position de n'importe quel point en millimètres.

Lancer : voir_table.bat (après regler_table.bat). Dans la fenêtre :
  - les marqueurs vus sont entourés en vert ; il faut les 4 pour mesurer ;
  - CLIQUER sur un point de l'image affiche sa position sur la table, l'angle du socle et la distance pour l'atteindre ;
  - touche Q pour quitter.
Le bras ne bouge pas : ce programme ne fait que regarder. Première étape de « prends le gobelet »."""
import argparse, sys
import cv2
import table as T

def dessiner(image, centres, contours, h, clics):
    for i, c in contours.items():
        cv2.polylines(image, [c.astype(int)], True, (0, 200, 0), 2)
        cv2.putText(image, str(i), (int(centres[i][0]) - 8, int(centres[i][1]) + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    if h is None:
        manque = [i for i in T.IDS if i not in centres]
        cv2.putText(image, f'Marqueurs manquants : {manque}', (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2); return
    cv2.circle(image, T.vers_image(h, 0, 0), 6, (255, 0, 0), -1)                       # l'axe du socle, s'il est dans l'image
    for (X, Y) in clics:
        a, d = T.pour_le_bras(X, Y); p = T.vers_image(h, X, Y)
        cv2.circle(image, p, 5, (0, 165, 255), -1)
        cv2.putText(image, f'X {X:+.0f}  Y {Y:+.0f} mm | socle {a:+.0f} deg, {d:.0f} mm', (p[0] + 8, p[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)
    cv2.putText(image, 'Table reperee : clique sur un point', (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 150, 0), 2)

def ech_fenetre(haut_image, haut_max):
    """De combien réduire l'image pour qu'elle tienne à l'écran (1.0 = pas de réduction). Les mesures se font sur l'image entière."""
    return min(1.0, haut_max / haut_image)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--camera', type=int, default=1)
    ap.add_argument('--large', type=int, default=1280); ap.add_argument('--haut', type=int, default=960)
    ap.add_argument('--fenetre', type=int, default=700, help='hauteur maximale de la fenêtre à l\'écran (points)'); a = ap.parse_args()
    reglage = T.charger()
    if not reglage: sys.exit('Réglage de la table introuvable : lance d\'abord regler_table.bat')
    cam = cv2.VideoCapture(a.camera, cv2.CAP_DSHOW) if sys.platform == 'win32' else cv2.VideoCapture(a.camera)
    if not cam.isOpened(): sys.exit(f'Caméra n° {a.camera} introuvable : essaie --camera 0, ou lance tete\\lister_cameras.bat')
    # Format 4/3 (1280 × 960) : c'est tout le capteur de la C270. En 16/9 (1280 × 720) la caméra coupe le haut et le bas de
    # l'image, donc elle voit moins de table (Nicolas, 24/11/2026 : « je ne vois pas tout »). --large 1280 --haut 720 pour revenir.
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, a.large); cam.set(cv2.CAP_PROP_FRAME_HEIGHT, a.haut)
    etat = {'h': None, 'clics': [], 'ech': 1.0}
    def souris(evt, x, y, *_):
        x, y = x / etat['ech'], y / etat['ech']                                    # la fenêtre peut être réduite : retour aux points de l'image
        if evt == cv2.EVENT_LBUTTONDOWN and etat['h'] is not None:
            X, Y = T.vers_table(etat['h'], x, y); ang, d = T.pour_le_bras(X, Y); etat['clics'] = (etat['clics'] + [(X, Y)])[-3:]
            print(f'Point : X = {X:+.0f} mm (droite), Y = {Y:+.0f} mm (avant) → socle à {ang:+.0f}°, à {d:.0f} mm de l\'axe du socle')
    cv2.namedWindow('Table de Calin'); cv2.setMouseCallback('Table de Calin', souris)
    print('Fenêtre ouverte. Clique sur un point de la table ; touche Q pour quitter.')
    vu = False
    while True:
        ok, image = cam.read()
        if not ok: print('La caméra ne répond plus.'); break
        centres, contours = T.detecter(image); h = T.passage(centres, reglage)
        if h is not None: etat['h'] = h
        dessiner(image, centres, contours, h, etat['clics'] if h is not None else [])
        if not vu: vu = True; print(f'Image de la caméra : {image.shape[1]} × {image.shape[0]} points.')
        etat['ech'] = ech_fenetre(image.shape[0], a.fenetre)
        cv2.imshow('Table de Calin', image if etat['ech'] == 1.0 else cv2.resize(image, None, fx=etat['ech'], fy=etat['ech'], interpolation=cv2.INTER_AREA))
        if cv2.waitKey(1) & 0xFF in (ord('q'), ord('Q')): break
    cam.release(); cv2.destroyAllWindows()

if __name__ == '__main__': main()
