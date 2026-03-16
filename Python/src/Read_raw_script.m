clc
clear

%%%%
DirPath = "C:\Users\Arthur\Documents\Linas_B\Measurement_data";
GainFolderPath = "Gain_list_2026_03_16_18_34";
FullPath = DirPath+"\"+GainFolderPath+"\";

PreambleNameStart = "PREAMBLE_CH"; %+channel_index
RawNameStart = "RAW_CH"; %+channel_index
UsedChannels = [1,2];
StartIndex = 100; %index start
StopIndex = 200; %index stop
StepIndex = 20;
CurrentIndex = 100;
%%%%
%% 

%create one figure
Fig = figure();
subplot(2,1,1)
title("CH1 reconstructed data")
xlabel("Time, s")
ylabel("Voltage, V")
hold on
subplot(2,1,2)
title("CH2 reconstructed data")
xlabel("Time, s")
ylabel("Voltage, V")
hold on
%% 
%read and process in a loop after
for channel = 1:length(UsedChannels)
    %format names of preamble and channel
    RawFileName = RawNameStart + UsedChannels(channel)+ "_" + CurrentIndex + ".bin"; % Construct the filename
    PreambleFileName = PreambleNameStart + UsedChannels(channel)+ "_" + CurrentIndex + ".txt";
    fprintf('Reading RAW file:%s\n', RawFileName);
    fprintf('Reading Preamble file:%s\n', PreambleFileName);

    raw_file = fopen(FullPath+RawFileName,'r');
    param_file = fopen(FullPath+PreambleFileName,'r');
    %no header, read full data
    raw_data = fread(raw_file,"uint16");
    % read preamble
    param_list = textscan(param_file,"%s",Delimiter=',');
    param_list=param_list{1,1};
    
    fclose(raw_file);
    fclose(param_file);

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

    %main arrays
    time_index = xincrement.*index;
    voltage_array = yincrement*(raw_data-yorigin-yreference);


    subplot(2,1,channel);
    plot(time_index,voltage_array)
    hold on

end