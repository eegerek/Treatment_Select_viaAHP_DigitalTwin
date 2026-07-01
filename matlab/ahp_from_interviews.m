function ahp_from_interviews
% AHP_FROM_INTERVIEWS  Build AHP pairwise matrices from raw interview data.
% =========================================================================
% PURPOSE (for re-verification of the manuscript's Tables 2-4)
%   Given the individual pairwise judgements collected from your interviewees,
%   this builds the GROUP pairwise-comparison matrix the correct way, screens
%   each respondent for consistency, derives the priority weights and the
%   consistency ratio, and prints them so you can compare against the
%   published tables.  If the output here disagrees with the published table,
%   the original construction was flawed.
%
% THE METHOD (brief, because the proper conventions are easy to get wrong)
%   * Each respondent compares every pair of items on Saaty's 1-9 ratio scale.
%     For items i and j, a_ij = how many times i is preferred to j; the matrix
%     is reciprocal (a_ji = 1/a_ij) with a_ii = 1.  You only enter the upper
%     triangle; the code fills the rest.
%   * CONSISTENCY SCREENING: each respondent's matrix gets a consistency ratio
%     (CR).  Saaty's rule is CR <= 0.10; respondents above that are dropped
%     (and reported), because inconsistent judgements pollute the group result.
%   * GROUP AGGREGATION = "AIJ" (Aggregation of Individual Judgements): the
%     group entry is the GEOMETRIC mean of the individual a_ij across kept
%     respondents.  Use the geometric (not arithmetic) mean: it is the only
%     mean that preserves reciprocity, i.e. geomean(a_ij) = 1/geomean(a_ji).
%     Arithmetic averaging breaks reciprocity and is a common error.
%   * The priority weights are the principal eigenvector of the group matrix.
%   * An alternative, "AIP" (Aggregation of Individual Priorities), computes
%     each respondent's weights first and then geometric-means the weight
%     vectors; provided as a cross-check (use when respondents are distinct
%     decision-makers rather than one synthetic group).
%
% Requires only base MATLAB. Mirrors dtahp/interviews.py in the Python package.
% =========================================================================

    % ----- name your items (order matters; must match the judgement order) -
    alts  = {'MBR','EC','CW'};                       % 3 alternatives
    crits = {'Eff','Cost','Land','Energy','Chem','Odor'};  % 6 criteria

    % =====================================================================
    % EXAMPLE 1 -- alternatives under ONE criterion (n = 3, pairs = 3)
    % Pair order for n=3 is (1,2),(1,3),(2,3) = (MBR,EC),(MBR,CW),(EC,CW).
    % Rows = respondents.  REPLACE the demo numbers with your interview data.
    % (Demo below approximates the 'Treatment Efficiency' matrix.)
    % =====================================================================
    J_eff = [ 9   5   1/3 ;     % respondent 1
              7   5   1/2 ;     % respondent 2
              9   4   1/3 ;     % respondent 3
              8   6   1/4 ;     % respondent 4
              9   5   1/3 ];    % respondent 5
    fprintf('--- EXAMPLE 1: alternatives under "Treatment Efficiency" ---\n');
    report(J_eff, 3, alts);

    % =====================================================================
    % EXAMPLE 2 -- criteria for ONE stakeholder group (n = 6, pairs = 15)
    % Pair order for n=6: (1,2)(1,3)(1,4)(1,5)(1,6)(2,3)(2,4)(2,5)(2,6)
    %                     (3,4)(3,5)(3,6)(4,5)(4,6)(5,6)
    % i.e. Eff-Cost, Eff-Land, Eff-Energy, Eff-Chem, Eff-Odor, Cost-Land, ...
    % Enter ONE row per interviewee (urban planners: 9 rows; residents: 30; ...)
    % The two demo rows are placeholders -- REPLACE WITH YOUR DATA.
    % =====================================================================
    J_crit = [ 5  6  2  1  3   2  1/2 1/3 1/2  1/3 1/2 1   2  3  2 ;   % planner 1
               4  5  2  2  3   1  1/2 1/2 1    1/2 1/2 1   1  2  2 ];  % planner 2
    fprintf('\n--- EXAMPLE 2: criteria weights for a stakeholder group ---\n');
    report(J_crit, 6, crits);

    fprintf(['\nTo re-verify the paper: paste each group''s real judgement rows\n' ...
             'into J_crit (criteria) and into six J_* blocks (alternatives, one\n' ...
             'per criterion), run, and compare the printed weights with Tables\n' ...
             '2-4.  Mismatches indicate the original matrices were mis-built.\n']);
end

% =========================================================================
function report(J, n, names)
    [Abar, w, CR, CRind, kept] = ahp_group(J, n);
    fprintf('respondents: %d total, %d kept (CR<=0.10), %d dropped\n', ...
            size(J,1), numel(kept), size(J,1)-numel(kept));
    fprintf('individual CRs: '); fprintf('%.3f ', CRind); fprintf('\n');
    fprintf('aggregated group matrix (AIJ, geometric mean):\n');
    disp(Abar);
    fprintf('priority weights (eigenvector):\n');
    for i = 1:n, fprintf('   %-7s %.4f\n', names{i}, w(i)); end
    fprintf('group consistency ratio CR = %.3f  (%s)\n', CR, ...
            tern(CR<=0.10,'acceptable','TOO HIGH (>0.10)'));
    wA = ahp_group_AIP(J, n);
    fprintf('cross-check (AIP, geomean of individual weights): ');
    fprintf('%.4f ', wA); fprintf('\n');
end
% -------------------------------------------------------------------------
function [Abar, w, CR, CRind, kept] = ahp_group(J, n, crthr)
% AIJ aggregation with per-respondent consistency screening.
    if nargin < 3, crthr = 0.10; end
    R = size(J,1);  P = n*(n-1)/2;
    assert(size(J,2)==P, 'each row needs n(n-1)/2 = %d judgements', P);
    CRind = zeros(R,1);
    for r = 1:R, [~, CRind(r)] = ahp_priority(build_recip(J(r,:), n)); end
    kept = find(CRind <= crthr);
    if isempty(kept)
        warning('no respondent met CR<=%.2f; keeping all', crthr); kept = (1:R)';
    end
    ubar = exp(mean(log(J(kept,:)), 1));      % geometric mean per pair (upper tri)
    Abar = build_recip(ubar, n);
    [w, CR] = ahp_priority(Abar);
end
% -------------------------------------------------------------------------
function w = ahp_group_AIP(J, n)
% AIP: priorities per respondent, then geometric mean of the weight vectors.
    R = size(J,1);  W = zeros(R,n);
    for r = 1:R, [W(r,:),~] = ahp_priority(build_recip(J(r,:), n)); end
    g = exp(mean(log(W),1));  w = g/sum(g);
end
% -------------------------------------------------------------------------
function A = build_recip(u, n)
% build full reciprocal matrix from an upper-triangular judgement vector u.
    A = eye(n);  idx = 1;
    for i = 1:n-1
        for j = i+1:n
            A(i,j) = u(idx);  A(j,i) = 1/u(idx);  idx = idx + 1;
        end
    end
end
% -------------------------------------------------------------------------
function [w, CR] = ahp_priority(A)
    RI = [0 0 0.58 0.90 1.12 1.24 1.32 1.41 1.45 1.49];   % Saaty random index
    n = size(A,1);
    [V,D] = eig(A);  [lmax,k] = max(real(diag(D)));
    w = abs(real(V(:,k)));  w = (w/sum(w)).';
    CI = (lmax - n)/(n - 1);
    if n <= numel(RI) && RI(n) > 0, CR = CI/RI(n); else, CR = CI; end
end
% -------------------------------------------------------------------------
function s = tern(c,a,b), if c, s=a; else, s=b; end, end
