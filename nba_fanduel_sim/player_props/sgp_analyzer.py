"""
Same Game Parlay (SGP) Analyzer

Analyzes correlations between player props in the same game.
Critical for accurate SGP pricing since outcomes are NOT independent.

Key correlations:
- Teammates scoring (negative correlation - limited possessions)
- Opponent props vs team total (positive correlation)
- Player scoring vs assists (slight negative for ball-dominant players)
- Team pace vs all props (positive correlation)
"""

import numpy as np
from scipy.stats import multivariate_normal, norm
from typing import List, Dict, Tuple
from dataclasses import dataclass
from itertools import combinations

from .player_stats_model import PlayerProjection


@dataclass
class SGPCorrelation:
    """Correlation between two props in a same game parlay"""

    prop1_player: str
    prop1_type: str
    prop2_player: str
    prop2_type: str

    correlation: float  # -1 to 1

    reason: str  # Explanation of correlation


@dataclass
class ParlayCombination:
    """A specific same game parlay combination"""

    props: List[Dict]  # List of prop bets
    combined_odds: int  # Parlay odds
    true_probability: float  # Accounting for correlations
    naive_probability: float  # Assuming independence
    edge: float  # true_prob - implied_prob
    adjusted_ev: float  # After reality checks

    correlation_impact: float  # How much correlation changes probability


class SGPAnalyzer:
    """
    Analyzes same game parlay opportunities.

    Accounts for correlations between props that bookmakers
    may misprice.
    """

    def __init__(self):
        """Initialize SGP analyzer"""
        pass

    def estimate_correlation(self,
                            prop1: Dict,
                            prop2: Dict,
                            game_context: Dict) -> SGPCorrelation:
        """
        Estimate correlation between two props in same game.

        Args:
            prop1: First prop dict with player, type, side
            prop2: Second prop dict
            game_context: Game information

        Returns:
            SGPCorrelation object
        """

        player1 = prop1['player']
        type1 = prop1['prop_type']
        player2 = prop2['player']
        type2 = prop2['prop_type']

        # Same player, different props
        if player1 == player2:
            return self._same_player_correlation(type1, type2, player1)

        # Teammates (same team)
        if self._are_teammates(player1, player2, game_context):
            return self._teammate_correlation(type1, type2, player1, player2)

        # Opponents
        if self._are_opponents(player1, player2, game_context):
            return self._opponent_correlation(type1, type2, player1, player2)

        # Default: weak correlation
        return SGPCorrelation(
            prop1_player=player1,
            prop1_type=type1,
            prop2_player=player2,
            prop2_type=type2,
            correlation=0.0,
            reason="No strong correlation identified"
        )

    def _same_player_correlation(self, type1: str, type2: str, player: str) -> SGPCorrelation:
        """Correlation between different props for same player"""

        # Points vs Assists (ball-dominant players)
        if {type1, type2} == {'points', 'assists'}:
            return SGPCorrelation(
                prop1_player=player,
                prop1_type=type1,
                prop2_player=player,
                prop2_type=type2,
                correlation=-0.15,
                reason="Scoring more usually means assisting less"
            )

        # Points vs Rebounds (big men)
        if {type1, type2} == {'points', 'rebounds'}:
            return SGPCorrelation(
                prop1_player=player,
                prop1_type=type1,
                prop2_player=player,
                prop2_type=type2,
                correlation=0.20,
                reason="Playing time correlates both stats"
            )

        # Points vs Threes
        if {type1, type2} == {'points', 'threes'}:
            return SGPCorrelation(
                prop1_player=player,
                prop1_type=type1,
                prop2_player=player,
                prop2_type=type2,
                correlation=0.40,
                reason="Threes directly contribute to points"
            )

        # Default: moderate positive (playing time)
        return SGPCorrelation(
            prop1_player=player,
            prop1_type=type1,
            prop2_player=player,
            prop2_type=type2,
            correlation=0.25,
            reason="Correlated through playing time"
        )

    def _teammate_correlation(self, type1: str, type2: str, player1: str, player2: str) -> SGPCorrelation:
        """Correlation between teammates' props"""

        # Scoring props (negative - finite possessions)
        if type1 in ['points', 'threes'] and type2 in ['points', 'threes']:
            return SGPCorrelation(
                prop1_player=player1,
                prop1_type=type1,
                prop2_player=player2,
                prop2_type=type2,
                correlation=-0.20,
                reason="Limited possessions - if one scores more, other scores less"
            )

        # Rebounds (negative - finite rebounds)
        if type1 == 'rebounds' and type2 == 'rebounds':
            return SGPCorrelation(
                prop1_player=player1,
                prop1_type=type1,
                prop2_player=player2,
                prop2_type=type2,
                correlation=-0.30,
                reason="Teammates compete for same rebounds"
            )

        # Assists (weak negative)
        if type1 == 'assists' and type2 == 'assists':
            return SGPCorrelation(
                prop1_player=player1,
                prop1_type=type1,
                prop2_player=player2,
                prop2_type=type2,
                correlation=-0.10,
                reason="Multiple playmakers can assist same baskets"
            )

        # Mixed stats (slightly positive - team performance)
        return SGPCorrelation(
            prop1_player=player1,
            prop1_type=type1,
            prop2_player=player2,
            prop2_type=type2,
            correlation=0.10,
            reason="Correlated through team performance"
        )

    def _opponent_correlation(self, type1: str, type2: str, player1: str, player2: str) -> SGPCorrelation:
        """Correlation between opponents' props"""

        # Scoring (positive - high-scoring games)
        if type1 in ['points', 'threes'] and type2 in ['points', 'threes']:
            return SGPCorrelation(
                prop1_player=player1,
                prop1_type=type1,
                prop2_player=player2,
                prop2_type=type2,
                correlation=0.25,
                reason="High-pace games benefit both teams' scorers"
            )

        # Mixed stats (weak positive)
        return SGPCorrelation(
            prop1_player=player1,
            prop1_type=type1,
            prop2_player=player2,
            prop2_type=type2,
            correlation=0.15,
            reason="Game flow affects both players"
        )

    def _are_teammates(self, player1: str, player2: str, game_context: Dict) -> bool:
        """Check if players are on same team"""
        # Simplified - would use actual roster data
        return False  # Placeholder

    def _are_opponents(self, player1: str, player2: str, game_context: Dict) -> bool:
        """Check if players are on opposing teams"""
        # Simplified - would use actual roster data
        return True  # Placeholder

    def calculate_parlay_probability(self,
                                    props: List[Dict],
                                    correlations: List[SGPCorrelation]) -> Tuple[float, float]:
        """
        Calculate true parlay probability accounting for correlations.

        Args:
            props: List of prop bets with probabilities
            correlations: List of correlations between props

        Returns:
            (true_probability, naive_probability)
        """

        # Naive probability (independence assumption)
        naive_prob = np.prod([p['probability'] for p in props])

        # If only 1 or 2 legs, correlation impact is minimal
        if len(props) <= 2:
            # Small adjustment for 2-leg parlays
            if len(props) == 2 and correlations:
                corr = correlations[0].correlation
                # Adjust based on correlation
                adjustment = 1 + (corr * 0.1)  # Max 10% adjustment
                true_prob = naive_prob * adjustment
            else:
                true_prob = naive_prob

            return true_prob, naive_prob

        # For 3+ legs, use multivariate normal approximation
        n_props = len(props)

        # Build correlation matrix
        corr_matrix = np.eye(n_props)

        for corr in correlations:
            # Find indices
            idx1 = next((i for i, p in enumerate(props)
                        if p['player'] == corr.prop1_player and p['prop_type'] == corr.prop1_type),
                       None)
            idx2 = next((i for i, p in enumerate(props)
                        if p['player'] == corr.prop2_player and p['prop_type'] == corr.prop2_type),
                       None)

            if idx1 is not None and idx2 is not None:
                corr_matrix[idx1, idx2] = corr.correlation
                corr_matrix[idx2, idx1] = corr.correlation

        # Convert probabilities to z-scores (normal approximation)
        z_scores = [norm.ppf(p['probability']) for p in props]

        # Calculate multivariate probability
        # Simplified: adjust naive probability by correlation factor
        avg_correlation = np.mean([abs(c.correlation) for c in correlations]) if correlations else 0

        # Positive correlation increases parlay probability
        # Negative correlation decreases it
        avg_signed_corr = np.mean([c.correlation for c in correlations]) if correlations else 0

        correlation_factor = 1 + (avg_signed_corr * 0.15 * len(props))
        true_prob = naive_prob * correlation_factor

        # Clamp to [0, 1]
        true_prob = max(0.0, min(1.0, true_prob))

        return true_prob, naive_prob

    def find_sgp_opportunities(self,
                              all_props: List[Dict],
                              game_context: Dict,
                              max_legs: int = 4,
                              min_odds: int = 200) -> List[ParlayCombination]:
        """
        Find +EV same game parlay opportunities.

        Args:
            all_props: All available props with edges
            game_context: Game information
            max_legs: Maximum number of legs in parlay
            min_odds: Minimum parlay odds to consider

        Returns:
            List of ParlayCombination objects with positive EV
        """

        opportunities = []

        # Filter to positive edge props
        positive_props = [p for p in all_props if p.get('best_edge', 0) > 0.03]

        if len(positive_props) < 2:
            return []

        # Generate combinations (2 to max_legs)
        for num_legs in range(2, min(max_legs + 1, len(positive_props) + 1)):
            for combo in combinations(positive_props, num_legs):
                combo_list = list(combo)

                # Calculate parlay odds
                parlay_odds = self._calculate_parlay_odds(combo_list)

                if parlay_odds < min_odds:
                    continue

                # Estimate correlations
                correlations = []
                for i in range(len(combo_list)):
                    for j in range(i + 1, len(combo_list)):
                        corr = self.estimate_correlation(
                            combo_list[i],
                            combo_list[j],
                            game_context
                        )
                        correlations.append(corr)

                # Calculate true probability
                true_prob, naive_prob = self.calculate_parlay_probability(
                    combo_list,
                    correlations
                )

                # Calculate edge
                from odds.fanduel_odds_utils import american_to_probability
                implied_prob = american_to_probability(parlay_odds)

                edge = true_prob - implied_prob

                # Only include if positive edge
                if edge > 0:
                    correlation_impact = true_prob - naive_prob

                    parlay = ParlayCombination(
                        props=combo_list,
                        combined_odds=parlay_odds,
                        true_probability=true_prob,
                        naive_probability=naive_prob,
                        edge=edge,
                        adjusted_ev=edge * 100,  # Simplified
                        correlation_impact=correlation_impact
                    )

                    opportunities.append(parlay)

        # Sort by edge
        opportunities.sort(key=lambda x: x.edge, reverse=True)

        return opportunities

    def _calculate_parlay_odds(self, props: List[Dict]) -> int:
        """Calculate combined American odds for parlay"""

        # Convert to decimal, multiply, convert back
        total_decimal = 1.0

        for prop in props:
            odds = prop.get('best_odds', -110)

            if odds > 0:
                decimal = (odds / 100) + 1
            else:
                decimal = (100 / abs(odds)) + 1

            total_decimal *= decimal

        # Convert back to American
        if total_decimal >= 2.0:
            american = (total_decimal - 1) * 100
        else:
            american = -100 / (total_decimal - 1)

        return int(american)


if __name__ == "__main__":
    # Example usage
    analyzer = SGPAnalyzer()

    # Example props
    prop1 = {'player': 'LeBron James', 'prop_type': 'points', 'probability': 0.55, 'best_odds': -110, 'best_edge': 0.05}
    prop2 = {'player': 'LeBron James', 'prop_type': 'assists', 'probability': 0.60, 'best_odds': -110, 'best_edge': 0.08}
    prop3 = {'player': 'Anthony Davis', 'prop_type': 'rebounds', 'probability': 0.58, 'best_odds': -110, 'best_edge': 0.06}

    # Estimate correlations
    corr1_2 = analyzer.estimate_correlation(prop1, prop2, {})
    print(f"Correlation: {prop1['player']} {prop1['prop_type']} vs {prop2['player']} {prop2['prop_type']}")
    print(f"  {corr1_2.correlation:.2f} - {corr1_2.reason}")
    print()

    # Calculate parlay probability
    props = [prop1, prop2, prop3]
    correlations = [corr1_2]

    true_prob, naive_prob = analyzer.calculate_parlay_probability(props, correlations)

    print(f"Parlay Probability:")
    print(f"  Naive (independent): {naive_prob*100:.1f}%")
    print(f"  True (correlated): {true_prob*100:.1f}%")
    print(f"  Impact: {(true_prob - naive_prob)*100:+.1f}%")
