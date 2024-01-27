from crispy_forms.layout import Layout, Row, Column, Fieldset, Field


class PointsPositifsCreationLayout(Layout):
    """Mise en page pour le formulaire de création
    d'utisateur."""

    def __init__(self):
        super().__init__(
            Fieldset(
                "Ajouter des points",
                Row(
                    Column(
                        Field(
                            "nb_positif",
                            placeholder="Nombre de points positifs",
                        )
                    ),
                    Column(Field("motif1", placeholder="Motif")),
                ),
                # Utilisez des classes css pour le style
                style="""
                    
                    margin-bottom: 1rem;
                """,
            ),
        )


class PointsNegatifsCreationLayout(Layout):
    """Mise en page pour le formulaire de création
    de points négatifs."""

    def __init__(self):
        super().__init__(
            Fieldset(
                "Enlever des points",
                Row(
                    Column(
                        Field(
                            "nb_negatif",
                            placeholder="Nombre de points négatifs",
                        )
                    ),
                    Column(Field("motif2", placeholder="Motif")),
                ),
                # Utilisez des classes css pour le style
                style="""
                    margin-bottom: 1rem;
                """,
            ),
        )
