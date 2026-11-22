# Photophore : ABox dont les 4 parois reçoivent des dessins découpés.
# Basé sur ABox de Boxes.py (Florian Festi, GPL v3 ou ultérieure).

from boxes import *
from boxes.generators.abox import ABox
from boxes.svgimport import aplatir


class Photophore(ABox):
    """Boîte simple dont les 4 parois portent des dessins découpés (photophore)"""

    description = "ABox avec dessins découpés dans les 4 parois."

    ui_group = "Box"

    def __init__(self) -> None:
        ABox.__init__(self)
        # Pour chaque paroi : None ou un boxes.svgimport.Dessin
        # (cadre démarrant en (0, 0), axe y vers le bas comme en SVG)
        self.dessins = [None, None, None, None]
        self.marge = 8.0
        self.empilable = False

    def _dessiner(self, i, largeur, hauteur, retrait_x):
        """Découpe le dessin n° i dans la zone pleine de la paroi (repère local : origine en bas à gauche)."""
        dessin = self.dessins[i]
        if not dessin:
            return
        bw, bh = dessin.largeur, dessin.hauteur
        dispo_l = largeur - 2 * (self.marge + retrait_x)
        dispo_h = hauteur - 2 * self.marge
        if dispo_l <= 0 or dispo_h <= 0:
            raise ValueError("Marge trop grande pour la paroi %d" % (i + 1))
        facteurs = []
        if bw > 0:
            facteurs.append(dispo_l / bw)
        if bh > 0:
            facteurs.append(dispo_h / bh)
        if not facteurs:
            return
        s = min(facteurs)
        ox = self.marge + retrait_x + (dispo_l - bw * s) / 2
        oy = self.marge + (dispo_h - bh * s) / 2

        ctx = self.ctx
        for sp in dessin.sous_chemins:
            pts = aplatir(sp, s)
            if len(pts) < 2:
                continue
            tr = lambda p: (ox + p[0] * s, oy + (bh - p[1]) * s)
            ctx.move_to(*tr(pts[0]))
            for p in pts[1:]:
                ctx.line_to(*tr(p))
            if sp["ferme"] and pts[-1] != pts[0]:
                ctx.line_to(*tr(pts[0]))
            ctx.stroke()

    def render(self):
        x, y, h = self.x, self.y, self.h
        t = self.thickness

        # s/S : trous de fixation du fond et pieds complémentaires en haut.
        # h/e : fond emboîté classique, haut droit.
        t1, t2, t3, t4 = ("SSSS" if self.empilable else "eeee")
        b = self.edges["s" if self.empilable else "h"]
        sideedge = "F"

        if self.outside:
            self.x = x = self.adjustSize(x, sideedge, sideedge)
            self.y = y = self.adjustSize(y)
            self.h = h = self.adjustSize(h, b, t1)

        hauteur_utile = h - b.startWidth() - self.edges[t1].startWidth()

        def cb(i, largeur, retrait_x):
            if not self.dessins[i]:
                return None
            return [lambda: self._dessiner(i, largeur, hauteur_utile, retrait_x), None, None, None]

        with self.saved_context():
            self.rectangularWall(x, h, [b, sideedge, t1, sideedge],
                                 ignore_widths=[1, 6], callback=cb(0, x, 0), move="up")
            self.rectangularWall(x, h, [b, sideedge, t3, sideedge],
                                 ignore_widths=[1, 6], callback=cb(1, x, 0), move="up")

            if self.bottom_edge != "e":
                self.rectangularWall(x, y, "ffff", move="up")
            self.lid(x, y)

        self.rectangularWall(x, h, [b, sideedge, t3, sideedge],
                             ignore_widths=[1, 6], move="right only")
        self.rectangularWall(y, h, [b, "f", t2, "f"],
                             ignore_widths=[1, 6], callback=cb(2, y, t), move="up")
        self.rectangularWall(y, h, [b, "f", t4, "f"],
                             ignore_widths=[1, 6], callback=cb(3, y, t), move="up")
