% =========================================================================
% AHP EVALUATION FOR GREYWATER TREATMENT SELECTION (MBR, EC, CW)
% -------------------------------------------------------------------------
% MATLAB companion to the Python package (dtahp). It reproduces the static
% AHP part: priority weights, consistency ratios, per-stakeholder global
% scores, and the consolidated ranking by geometric mean.
%
%   >>> EXAMPLE / TEMPLATE DATA BELOW -- SYNTHETIC PLACEHOLDER VALUES. <<<
%   >>> Replace every matrix with your own elicited judgements before  <<<
%   >>> drawing any conclusion. The numbers here are not from a study;  <<<
%   >>> they are internally consistent (CR < 0.02) and exist only so    <<<
%   >>> that the script runs out of the box.                            <<<
% =========================================================================

% Saaty's Random Index (RI): index n is the RI for an n x n matrix.
RI_dict = [0, 0, 0.58, 0.90, 1.12, 1.24, 1.32, 1.41, 1.45];

% --- Part A: alternative comparisons under each criterion (MBR, EC, CW) ---
A_eff    = [1,   1/2, 1  ;  2,   1,   2  ;  1,   1/2, 1  ];
A_cost   = [1,   2,   1/3;  1/2, 1,   1/4;  3,   4,   1  ];
A_land   = [1,   1,   1/2;  1,   1,   1/3;  2,   3,   1  ];
A_energy = [1,   1,   4  ;  1,   1,   3  ;  1/4, 1/3, 1  ];
A_chem   = [1,   1/9, 1/3;  9,   1,   4  ;  3,   1/4, 1  ];
A_odor   = [1,   7,   3  ;  1/7, 1,   1/2;  1/3, 2,   1  ];

Alt_Matrices   = {A_eff, A_cost, A_land, A_energy, A_chem, A_odor};
criteria_names = {'Efficiency','Cost','Land','Energy','Chemical','Odor'};
alt_names      = {'MBR','EC','CW'};
stakeholders   = {'Urban Planners (UP)','Residents & Workers (RW)','Industry Operators (IO)'};

% --- Part B: criteria comparisons per stakeholder group (6x6) ------------
S_UP = [1,   1/2, 1/5, 1,   1/2, 1/3;
        2,   1,   1/4, 2,   1,   1/2;
        5,   4,   1,   6,   3,   2  ;
        1,   1/2, 1/6, 1,   1/2, 1/3;
        2,   1,   1/3, 2,   1,   1/2;
        3,   2,   1/2, 3,   2,   1  ];

S_RW = [1,   1,   1,   1/2, 1,   1/2;
        1,   1,   1,   1/2, 1,   1/2;
        1,   1,   1,   1/2, 1,   1/2;
        2,   2,   2,   1,   2,   1  ;
        1,   1,   1,   1/2, 1,   1/2;
        2,   2,   2,   1,   2,   1  ];

S_IO = [1,   1,   1,   1/3, 2,   1/2;
        1,   1,   1,   1/3, 2,   1/2;
        1,   1,   1,   1/3, 2,   1/2;
        3,   3,   3,   1,   6,   1  ;
        1/2, 1/2, 1/2, 1/6, 1,   1/4;
        2,   2,   2,   1,   4,   1  ];

Stakeholder_Matrices = {S_UP, S_RW, S_IO};

%% Parts 1 & 2 -- alternative weights and CRs (3x3) -----------------------
fprintf('PARTS 1 & 2: ALTERNATIVE PAIRWISE COMPARISONS (3x3)\n');
W_alternatives = zeros(3, 6);
for i = 1:6
    [w, cr] = ahp_compute(Alt_Matrices{i}, RI_dict(3));
    W_alternatives(:, i) = w;
    verdict = 'consistent'; if cr >= 0.1, verdict = 'INCONSISTENT'; end
    fprintf('  %-12s CR = %.4f (%s) | w = [%.4f %.4f %.4f]\n', ...
        criteria_names{i}, cr, verdict, w(1), w(2), w(3));
end

%% Parts 3 & 4 -- stakeholder criteria weights and CRs (6x6) --------------
fprintf('\nPARTS 3 & 4: STAKEHOLDER CRITERIA PRIORITIES (6x6)\n');
W_criteria_stakeholders = zeros(6, 3);
for s = 1:3
    [w_crit, cr_crit] = ahp_compute(Stakeholder_Matrices{s}, RI_dict(6));
    W_criteria_stakeholders(:, s) = w_crit;
    verdict = 'consistent'; if cr_crit >= 0.1, verdict = 'INCONSISTENT'; end
    fprintf('  %-26s CR = %.4f (%s)\n', stakeholders{s}, cr_crit, verdict);
end

%% Parts 5 & 6 -- global score matrix ------------------------------------
Global_Score_Matrix = W_alternatives * W_criteria_stakeholders;   % alt x stakeholder
fprintf('\nPARTS 5 & 6: GLOBAL SCORES (rows = alternatives)\n');
for a = 1:3
    fprintf('  %-5s', alt_names{a});
    fprintf('%10.4f', Global_Score_Matrix(a, :)); fprintf('\n');
end

%% Part 7 -- consolidated ranking by geometric mean ----------------------
geom_means = prod(Global_Score_Matrix, 2) .^ (1/3);
consolidated = geom_means / sum(geom_means);
fprintf('\nPART 7: CONSOLIDATED RANKING (geometric mean)\n');
for a = 1:3
    fprintf('  %-5s  %.4f (%.1f%%)\n', alt_names{a}, consolidated(a), 100*consolidated(a));
end
[~, best] = max(consolidated);
fprintf('  >> recommendation across all stakeholders: %s\n', alt_names{best});

%% Eigenvector AHP solver ------------------------------------------------
function [w, cr] = ahp_compute(Mat, RI)
    [V, D] = eig(Mat);
    [lambda_max, idx] = max(real(diag(D)));
    w = abs(real(V(:, idx)));
    w = w / sum(w);
    n = size(Mat, 1);
    if n <= 2
        cr = 0;
    else
        ci = (lambda_max - n) / (n - 1);
        cr = real(ci / RI);
    end
end
