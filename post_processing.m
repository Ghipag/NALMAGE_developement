close all
clear all

% loading data
run_1b_trace_data = readtable('data/run_1B_info.csv');
run_2b_trace_data = readtable('data/run_2B_info.csv');
run_1b_align_data = readtable('data/run_1b_reduced_alignment_Info.csv');
run_2b_align_data = readtable('data/run_2b_reduced_alignment_Info.csv');

%average traceability for element generation
average_overall_traceability_1b = mean(run_1b_trace_data.Manual_Rating);
average_overall_traceability_2b = mean(run_2b_trace_data.Manual_Rating);

%average traceability for interfaces
power_trace_1b = mean(list_ratings_with_skips(run_1b_trace_data.power_interfaces_1));
power_trace_2b = mean(list_ratings_with_skips(run_2b_trace_data.power_interfaces_1));

data_trace_1b = mean(list_ratings_with_skips(run_1b_trace_data.data_interfaces_1));
data_trace_2b = mean(list_ratings_with_skips(run_2b_trace_data.data_interfaces_1));

mechanical_trace_1b = mean(list_ratings_with_skips(run_1b_trace_data.mechanical_interfaces_1));
mechanical_trace_2b = mean(list_ratings_with_skips(run_2b_trace_data.mechanical_interfaces_1));

fluid_trace_1b = mean(list_ratings_with_skips(run_1b_trace_data.fluid_interfaces_1));
fluid_trace_2b = mean(list_ratings_with_skips(run_2b_trace_data.fluid_interfaces_1));

thermal_trace_1b = mean(list_ratings_with_skips(run_1b_trace_data.thermal_interfaces_1));
thermal_trace_2b = mean(list_ratings_with_skips(run_2b_trace_data.thermal_interfaces_1));

section_heatmap(table2array(run_1b_align_data(1:end,2:end))*1/3,transpose(run_1b_align_data.Properties.VariableNames(2:end)),transpose(run_1b_align_data.Var1),1,height(run_1b_align_data),1,width(run_1b_align_data)-1)
disp('***')
section_heatmap(table2array(run_2b_align_data(1:end,2:end))*1/3,transpose(run_2b_align_data.Properties.VariableNames(2:end)),transpose(run_2b_align_data.Var1),1,height(run_2b_align_data),1,width(run_2b_align_data)-1)

% rating agreement


x_matrix = sort_data(run_1b_trace_data.Manual_Rating(17:end),run_1b_trace_data.rating(17:end),3);

disp('run 1b')
kappa(x_matrix,1)

x_matrix = sort_data(run_2b_trace_data.Manual_Rating,run_2b_trace_data.rating,3);

disp('disp 2b')
kappa(x_matrix,1)

% PROVE_align_ass1 = [1; 1; 1; 3]
% PROVE_align_ass2 = [1; 1; 3; 3]
% x_matrix = sort_data(PROVE_align_ass1,PROVE_align_ass2)
% 
% kappa(x_matrix,1)

% old data 
% TRUTHS traceability
data = [70.0	54.5	66.0	82.7
85.3	81.8	91.5	84.0
72.1	67.3	61.7	81.5
94.0	90.9	97.9	93.8];

[ass_1_TRUTHS, ass_2_TRUTHS] =  compute_traceability_datasets(data);
averaged_trace = (ass_1_TRUTHS + ass_2_TRUTHS)/2;

% TRUTHS alignment
data = [2.4146	0 2.4286	2.4118
1.7561	0 2.1429	1.5882
2.1977	0 2.5556	2.1029
1.907	0 2.6667	1.7059];

[ass_1_TRUTHS, ass_2_TRUTHS] =  compute_align_datasets(data);
averaged_pres_recall = (ass_1_TRUTHS + ass_2_TRUTHS)/2;

% TRUTHS alignment
data = [1.526	0	0.9428	1.6891
1.0675	0	0.9428	1.0572
1.1791	0	1.3093	1.1504
1.2198	0	1.4142	1.1632
0.3836	0	-0.3665	0.5386
-0.1523	0	-0.4714	-0.106];

[ass_1_TRUTHS, ass_2_TRUTHS] =  compute_specificity_datasets(data);
averaged_spec = (ass_1_TRUTHS + ass_2_TRUTHS)/2;

function section_heatmap(cdata,design_elements,generated_elements,gen1,gen2,des1,des2)
    x_names ={design_elements{des1:des2,1}};
    y_names = {generated_elements{1,gen1:gen2}};
    cdata = cdata(gen1:gen2,des1:des2);
    noramlization_type = 1;
    if noramlization_type == 1
        % noramlize by each row
        normalisation_coefs_rows = [];
        averaged_alignments_rows = [];
        for i = 1:size(cdata,1)
            normalisation_coefs_rows(i)= nnz(cdata(i,1:end));
            if normalisation_coefs_rows(i) == 0 
                normalisation_coefs_rows(i) = 1;
            end
            averaged_alignments_rows(i) = sum(cdata(i,1:end))/normalisation_coefs_rows(i);
        end
        % normalize by each collum
        normalisation_coefs_cols = [];
        averaged_alignments_cols = [];
        for i = 1:size(cdata,2)
            normalisation_coefs_cols(i)= nnz(cdata(1:end,i));
            if normalisation_coefs_cols(i) == 0 
                normalisation_coefs_cols(i) = 1;
            end
            averaged_alignments_cols(i) = sum(cdata(1:end,i))/normalisation_coefs_cols(i);
        end
        c_data_section_rows= cdata ./ transpose(normalisation_coefs_rows);
        c_data_section_cols= cdata ./ normalisation_coefs_cols;
%         jaccard_index = sum(sum(c_data_section_rows))/(size(x_names,2) + size(y_names,2)-sum(sum(c_data_section_rows)))
%         Sorensen_Dice_coef = 2*sum(sum(c_data_section_rows))/(size(x_names,2) + size(y_names,2))
%         jaccard_index = sum(sum(c_data_section_cols))/(size(x_names,2) + size(y_names,2)-sum(sum(c_data_section_cols)))
%         Sorensen_Dice_coef = 2*sum(sum(c_data_section_cols))/(size(x_names,2) + size(y_names,2))
        average_score_precision = mean(averaged_alignments_rows)*3
        average_score_recall = mean(averaged_alignments_cols)*3
        
        % now looking at "specifity"
        %cdata = [1 0 0 0 0; 0 1 0 0 0; 0 0 1 0 0; 0 0 0 1 0; 0 0 0 0 1]
        % convert to binary similarity
        c_data_binarized = zeros(size(cdata));
        for i = 1:size(cdata,1)
            for j = 1:size(cdata,2)
                if cdata(i,j)*3 >= 2
                    c_data_binarized(i,j) = 1;
                end
            end
        end
        

        gen_shared_values = [];
        for i = 1:size(cdata,1)
            gen_shared_values(i) = sum(c_data_binarized(i,1:end));
        end

        des_shared_values = [];
        for i = 1:size(cdata,2)
            des_shared_values(i) = sum(c_data_binarized(1:end,i));
        end
        under_specifcation_parameter = norm(gen_shared_values)/(size(cdata,1))^0.5
        over_specifcation_parameter = norm(des_shared_values)/(size(cdata,2))^0.5
        net_specification = over_specifcation_parameter - under_specifcation_parameter
%         specification = over_specifcation_parameter / under_specifcation_parameter
%       specificty = over_specifcation_factor/under_specifcation_factor
%         numerator = min([gen_shared_values,des_shared_values]);
%         demoninator = 1;
%         if max([gen_shared_values,des_shared_values]) ~= 0
%             demoninator = max([gen_shared_values,des_shared_values]);
%         end
        %Jaccard_index = numerator/demoninator
        %Sorensen_Dice_coef = 2*sum(sum(c_data_binarized))/(size(x_names,2) + size(y_names,2))


    end
%     figure
%     hold off
%     h = heatmap(x_names,y_names,cdata.*3);

end

function [ass_1, ass_2] = compute_traceability_datasets(unsorted_data)
    ass_1_3 = unsorted_data(1,:);
    ass_1_2 = unsorted_data(2,:)-unsorted_data(1,:);
    ass_1_1 = 100 - unsorted_data(2,:);
    ass_2_3 = unsorted_data(3,:);
    ass_2_2 = unsorted_data(4,:)-unsorted_data(3,:);
    ass_2_1 = 100 - unsorted_data(4,:);
    ass_1 = [ass_1_3;ass_1_2;ass_1_1];
    ass_2 = [ass_2_3;ass_2_2;ass_2_1];
end

function [ass_1, ass_2] = compute_align_datasets(unsorted_data)
    ass_1 = [unsorted_data(1,:);unsorted_data(3,:)];
    ass_2 = [unsorted_data(2,:);unsorted_data(4,:)];
end

function [ass_1, ass_2] = compute_specificity_datasets(unsorted_data)
    ass_1 = [unsorted_data(1,:);unsorted_data(3,:);unsorted_data(5,:)];
    ass_2 = [unsorted_data(2,:);unsorted_data(4,:);unsorted_data(6,:)];
end

function [completed_processed_ratings] = list_ratings_with_skips(ratings)
    processed_ratings = [];
    for i = 1:size(ratings,1)
        current_rating = ratings(i);
        if current_rating{1} ~= 'NONE'
            processed_ratings(end+1) = str2num(current_rating{1});
        end
    end
    completed_processed_ratings = processed_ratings;
end


function x_matrix = sort_data(ass1_data,ass2_data,order)
    x_matrix_working = zeros(order,order);
    for i = 1:size(x_matrix_working,1)
        for j = 1:size(x_matrix_working,2)
            classifacation_value_1 = i;
            classifacation_value_2 = j;
            counts = 0;
            % collect counts for current classifiacation
            for k = 1:size(ass1_data,1)
                if ass1_data(k) == classifacation_value_1 && ass2_data(k) == classifacation_value_2
                    counts = counts + 1;
                end
            end
            x_matrix_working(i,j) = counts;
    
        end
    end
    x_matrix =x_matrix_working;
end

function kappa(x,varargin)
% KAPPA: This function computes the Cohen's kappa coefficient.
% Cohen's kappa coefficient is a statistical measure of inter-rater
% reliability. It is generally thought to be a more robust measure than
% simple percent agreement calculation since k takes into account the
% agreement occurring by chance.
% Kappa provides a measure of the degree to which two judges, A and B,
% concur in their respective sortings of N items into k mutually exclusive
% categories. A 'judge' in this context can be an individual human being, a
% set of individuals who sort the N items collectively, or some non-human
% agency, such as a computer program or diagnostic test, that performs a
% sorting on the basis of specified criteria.
% The original and simplest version of kappa is the unweighted kappa
% coefficient introduced by J. Cohen in 1960. When the categories are
% merely nominal, Cohen's simple unweighted coefficient is the only form of
% kappa that can meaningfully be used. If the categories are ordinal and if
% it is the case that category 2 represents more of something than category
% 1, that category 3 represents more of that same something than category
% 2, and so on, then it is potentially meaningful to take this into
% account, weighting each cell of the matrix in accordance with how near it
% is to the cell in that row that includes the absolutely concordant items.
% This function can compute a linear weights or a quadratic weights.
%
% Syntax: 	kappa(X,W,ALPHA)
%      
%     Inputs:
%           X - square data matrix
%           W - Weight (0 = unweighted; 1 = linear weighted; 2 = quadratic
%           weighted; Default=0)
%           ALPHA - default=0.05.
%
%     Outputs:
%           - Observed agreement percentage
%           - Random agreement percentage
%           - Agreement percentage due to true concordance
%           - Residual not random agreement percentage
%           - Cohen's kappa 
%           - kappa error
%           - kappa confidence interval
%           - Maximum possible kappa
%           - k observed as proportion of maximum possible
%           - k benchmarks by Landis and Koch 
%           - z test results
%
%      Example: 
%
%           x=[88 14 18; 10 40 10; 2 6 12];
%
%           Calling on Matlab the function: kappa(x)
%
%           Answer is:
%
% UNWEIGHTED COHEN'S KAPPA
% --------------------------------------------------------------------------------
% Observed agreement (po) = 0.7000
% Random agreement (pe) = 0.4100
% Agreement due to true concordance (po-pe) = 0.2900
% Residual not random agreement (1-pe) = 0.5900
% Cohen's kappa = 0.4915
% kappa error = 0.0549
% kappa C.I. (alpha = 0.0500) = 0.3839     0.5992
% Maximum possible kappa, given the observed marginal frequencies = 0.8305
% k observed as proportion of maximum possible = 0.5918
% Moderate agreement
% z (k/kappa error) = 8.8347    p = 0.0000
% Reject null hypotesis: observed agreement is not accidental
%
%           Created by Giuseppe Cardillo
%           giuseppe.cardillo-edta@poste.it
%
% To cite this file, this would be an appropriate format:
% Cardillo G. (2007) Cohen's kappa: compute the Cohen's kappa ratio on a square matrix.   
% http://www.mathworks.com/matlabcentral/fileexchange/15365
%Input Error handling
p = inputParser;
addRequired(p,'x',@(x) validateattributes(x,{'numeric'},{'square','nonempty','integer','real','finite','nonnan','nonnegative'}));
addOptional(p,'w',0, @(x) isnumeric(x) && isreal(x) && isfinite(x) && isscalar(x) && ismember(x,[0 1 2]));
addOptional(p,'alpha',0.05, @(x) validateattributes(x,{'numeric'},{'scalar','real','finite','nonnan','>',0,'<',1}));
parse(p,x,varargin{:});
x=p.Results.x; w=p.Results.w; alpha=p.Results.alpha;
clear p default* validation*
m=size(x,1);
tr=repmat('-',1,80);
switch w
    case 0
        f=diag(ones(1,m)); %unweighted
        disp('UNWEIGHTED COHEN''S KAPPA')
        disp(tr)
        kcomp;
        disp(' ')
    case 1
        J=repmat((1:1:m),m,1);
        I=flipud(rot90(J));
        f=1-abs(I-J)./(m-1); %linear weight
        disp('LINEAR WEIGHTED COHEN''S KAPPA')
        disp(tr)
        kcomp;
        disp(' ')
    case 2
        J=repmat((1:1:m),m,1);
        I=flipud(rot90(J));
        f=1-((I-J)./(m-1)).^2; %quadratic weight
        disp('QUADRATIC WEIGHTED COHEN''S KAPPA')
        disp(tr)
        kcomp;
end
    function kcomp
        n=sum(x(:)); %Sum of Matrix elements
        x=x./n; %proportion
        r=sum(x,2); %rows sum
        s=sum(x); %columns sum
        Ex=r*s; %expected proportion for random agree
        po=sum(sum(x.*f)); %proportion observed
        pe=sum(sum(Ex.*f)); %proportion expected
        k=(po-pe)/(1-pe); %Cohen's kappa
        pom=sum(min([r';s])); %maximum proportion observable
        km=(pom-pe)/(1-pe); %maximum possible kappa, given the observed marginal frequencies
        ratio=k/km; %observed as proportion of maximum possible
        sek=sqrt((po*(1-po))/(n*(1-pe)^2)); %kappa standard error for confidence interval
        ci=k+([-1 1].*(abs(-realsqrt(2)*erfcinv(alpha))*sek)); %k confidence interval
        z=k/sek; %normalized kappa
        p=(1-0.5*erfc(-abs(z)/realsqrt(2)))*2;
        %display results
        fprintf('Observed agreement (po) = %0.4f\n',po)
        fprintf('Random agreement (pe) = %0.4f\n',pe)
        fprintf('Agreement due to true concordance (po-pe) = %0.4f\n',po-pe)
        fprintf('Residual not random agreement (1-pe) = %0.4f\n',1-pe)
        fprintf('Cohen''s kappa = %0.4f\n',k)
        fprintf('kappa error = %0.4f\n',sek)
        fprintf('kappa C.I. (alpha = %0.4f) = %0.4f     %0.4f\n',alpha,ci)
        fprintf('Maximum possible kappa, given the observed marginal frequencies = %0.4f\n',km)
        fprintf('k observed as proportion of maximum possible = %0.4f\n',ratio)
        if k<0
            disp('Poor agreement')
        elseif k>=0 && k<=0.2
            disp('Slight agreement')
        elseif k>=0.21 && k<=0.4
            disp('Fair agreement')
        elseif k>=0.41 && k<=0.6
            disp('Moderate agreement')
        elseif k>=0.61 && k<=0.8
            disp('Substantial agreement')
        elseif k>=0.81 && k<=1
            disp('Perfect agreement')
        end
        fprintf('z (k/kappa error) = %0.4f    p = %0.4f\n',z,p)
        if p<alpha
            disp('Reject null hypotesis: observed agreement is not accidental')
        else
            disp('Accept null hypotesis: observed agreement is accidental')
        end
    end
end
