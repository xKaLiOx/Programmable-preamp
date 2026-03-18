clc
clear

%%%%
DirPath = "C:\Users\Arthur\Documents\Linas_B\Measurement_data";
GainFolderPath = "Gain_list_2026_03_18_19_45";
FullPath = DirPath+"\"+GainFolderPath+"\";

PreambleNameStart = "PREAMBLE_CH"; %+channel_index
RawNameStart = "RAW_CH"; %+channel_index
UsedChannels = [1,2];

DACParamName = "DACIndex.txt";
%read start stop step values
DAC_param_file = fopen(FullPath+DACParamName);
DAC_param_list = textscan(DAC_param_file,"%s",Delimiter=',');

StartIndex = str2double(DAC_param_list{1}{2}); %DAC index start
StopIndex = str2double(DAC_param_list{1}{4}); %DAC index stop
StepIndex = str2double(DAC_param_list{1}{3});
%%%%
%%%%
%SWC frequency:
f_measurement = 1e6;%1 MHz sine from generator
%preallocating variables
Uest = zeros(1,length(UsedChannels));
Umag = zeros(1,length(UsedChannels));
Uph_deg = zeros(1,length(UsedChannels));

GainIndex = uint16(StartIndex:StepIndex:StopIndex-1);
Gain = zeros(1,length(GainIndex));


%%%%

%%%%
%printing the list from Start to Stop with zeroes included
PRINT_WITH_ZEROS = true;
PLOT_LAST = false;
%%

%create one figure
if PLOT_LAST == true
    Fig = figure();
    % subplot(2,1,1)
    % title("CH1 reconstructed data")
    % xlabel("Time, s")
    % ylabel("Voltage, V")
    % hold on
    % subplot(2,1,2)
    title("CH2 reconstructed data")
    xlabel("Time, s")
    ylabel("Voltage, V")
    hold on
end
%%
for CurrentIndex = 1:length(Gain)

    %read and process in a loop after
    for channel = 1:length(UsedChannels)
        %format names of preamble and channel
        RawFileName = RawNameStart + UsedChannels(channel)+ "_" + GainIndex(CurrentIndex) + ".bin"; % Construct the filename
        PreambleFileName = PreambleNameStart + UsedChannels(channel)+ "_" + GainIndex(CurrentIndex) + ".txt";
        fprintf('Reading RAW file:%s\n', RawFileName);
        fprintf('Reading Preamble file:%s\n', PreambleFileName);

        raw_file = fopen(FullPath+RawFileName,'r');
        param_file = fopen(FullPath+PreambleFileName,'r');
        %no header, read full data
        raw_data = fread(raw_file,"uint16");
        % read preamble
        premable_list = textscan(param_file,"%s",Delimiter=',');
        premable_list=premable_list{1,1};

        fclose(raw_file);
        fclose(param_file);

        if numel(premable_list) ~= 10
            error('Parameter list must contain 10 values.');
        end
        %parse the list
        format = str2double(premable_list{1});
        type = str2double(premable_list{2});
        points = str2double(premable_list{3});
        count = str2double(premable_list{4});
        xincrement = str2double(premable_list{5});
        xorigin = str2double(premable_list{6});
        xreference = str2double(premable_list{7});
        yincrement = str2double(premable_list{8});
        yorigin = str2double(premable_list{9});
        yreference = str2double(premable_list{10});


        if points ~= length(raw_data)
            error('Point and raw data does not match');
        end
        %create time index and voltages
        index = 0:1:points-1;

        %main arrays
        time_index = xincrement.*index;
        %voltage array is rows vector, transpose to get column array with .'
        voltage_array = (yincrement*(raw_data-yorigin-yreference)).';

        %calculate amplitude and phase using SWC
        Uest(channel) = SWCtruncated(time_index,2*pi*f_measurement,voltage_array);
        Umag(channel)=abs(Uest(channel));
        Uph_rad=angle(Uest(channel));
        Uph_deg(channel)=Uph_rad/pi*180;
    end
    Gain(CurrentIndex) = Umag(2)/Umag(1);
end

%%%%%%%%%%%%%%%%%%%
if PLOT_LAST == true
    plot(time_index,voltage_array)
end

%AFTER INDEXING LOOP
if PRINT_WITH_ZEROS == true
    disp("Printing gain list to a file")
    save Gain_characteristic Gain GainIndex;
else
    disp("NOT GOOD")
end