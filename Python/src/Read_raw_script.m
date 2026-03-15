clc
clear

%%%%
DirPath = "C:\Users\Linas\Desktop\univero_darbai\Bakalaurinis\Measurements\";
% DirPath = "C:/Users/Arthur/Documents/Linas_B/Measurement_data/";
FileName = "RAW_CH1_2026_03_13_19_39_54.bin";
ParamName = "Received_params_2026_03_13_19_39_42.txt";
%%%%

raw_file = fopen(DirPath+FileName,'r');
param_file = fopen(DirPath+ParamName,'r');
%no header, read full data
raw_data = fread(raw_file,"uint16");

% read preamble
param_list = textscan(param_file,"%s",Delimiter=',');
param_list=param_list{1,1};

if numel(param_list) ~= 10
    error('Parameter list must contain 10 values.');
end
%parse the list
format = str2double(param_list{1});
type = str2double(param_list{2});
points = str2double(param_list{3});
count = str2double(param_list{4});
xincrement = str2double(param_list{5});
xorigin = str2double(param_list{6});
xreference = str2double(param_list{7});
yincrement = str2double(param_list{8});
yorigin = str2double(param_list{9});
yreference = str2double(param_list{10});


if points ~= length(raw_data)
    error('Point and raw data does not match');
end
%create time index and voltages
index = 0:1:points-1;
time_index = xincrement.*index;
voltage_array = yincrement*(raw_data-yorigin-yreference);
plot(time_index,voltage_array)

fclose(raw_file);
fclose(param_file);