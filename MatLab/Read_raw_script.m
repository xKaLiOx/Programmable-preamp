


%% 
clc
clear


MEASUREMENT_TYPE = "BODE_PLOT"; %or GAIN_LIST
USE_AS_COMPENSATION_CURVE = true;
%%%%
DirPath = "C:\Users\Arthur\Documents\Linas_B\Measurement_data";
GainFolderPath = "Bode_plot_2026_03_23_15_58";
FullPath = DirPath+"\"+GainFolderPath+"\";

PreambleNameStart = "PREAMBLE_CH"; %+channel_index
RawNameStart = "RAW_CH"; %+channel_index
UsedChannels = [1,2];

ParamName = "ParameterList.txt";
%read start stop step values
ParamFile = fopen(FullPath+ParamName);
Param_list = textscan(ParamFile,"%s",Delimiter='\n');

%preallocating variables
Uest = zeros(1,length(UsedChannels));
Umag = zeros(1,length(UsedChannels));
Uph_deg = zeros(1,length(UsedChannels));

%% 
if MEASUREMENT_TYPE == "GAIN_LIST"
    disp("Starting gain list analysis")
    DAC_param_list = split(Param_list{1}(1),',');
    attenuator_param_list = split(Param_list{1}(2),',');
    
    input_attenuation_dB = str2double(attenuator_param_list{2});
    
    StartIndex = str2double(DAC_param_list{2}); %DAC index start
    StepIndex = str2double(DAC_param_list{3});
    StopIndex = str2double(DAC_param_list{4}); %DAC index stop
    %SWC frequency:
    f_measurement = 1e6;%1 MHz sine from generator
    GainIndex = uint16(StartIndex:StepIndex:StopIndex-1);
    Gain = zeros(1,length(GainIndex));

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
            preamble_list = textscan(param_file,"%s",Delimiter=',');
            preamble_list=preamble_list{1,1};
    
            fclose(raw_file);
            fclose(param_file);
    
            if numel(preamble_list) ~= 10
                error('Parameter list must contain 10 values.');
            end
            %parse the list
            format = str2double(preamble_list{1});
            type = str2double(preamble_list{2});
            points = str2double(preamble_list{3});
            count = str2double(preamble_list{4});
            xincrement = str2double(preamble_list{5});
            xorigin = str2double(preamble_list{6});
            xreference = str2double(preamble_list{7});
            yincrement = str2double(preamble_list{8});
            yorigin = str2double(preamble_list{9});
            yreference = str2double(preamble_list{10});
    
    
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
    %AFTER INDEXING LOOP
    disp("Printing gain list to a file")
    save Gain_characteristic Gain GainIndex;


elseif MEASUREMENT_TYPE == "BODE_PLOT"

    disp("Starting bode plot analysis")
    Frequency_list = str2double(split(Param_list{1}{1},','));
    Frequency_list = Frequency_list(2:end);%remove first value (string)
    attenuator_param_list = split(Param_list{1}{2},',');
    input_attenuation_dB = str2double(attenuator_param_list{2});

    Gain = zeros(1,length(Frequency_list));
    Phase = zeros(1,length(Frequency_list));
    for CurrentIndex = 1:length(Frequency_list)
        %read and process in a loop after
        for channel = 1:length(UsedChannels)
            %format names of preamble and channel
            RawFileName = RawNameStart + UsedChannels(channel)+ "_" + Frequency_list(CurrentIndex) + ".bin"; % Construct the filename
            PreambleFileName = PreambleNameStart + UsedChannels(channel)+ "_" + Frequency_list(CurrentIndex) + ".txt";
            fprintf('Reading RAW file:%s\n', RawFileName);
            fprintf('Reading Preamble file:%s\n', PreambleFileName);
    
            raw_file = fopen(FullPath+RawFileName,'r');
            param_file = fopen(FullPath+PreambleFileName,'r');
            %no header, read full data
            raw_data = fread(raw_file,"uint16");
            % read preamble
            preamble_list = textscan(param_file,"%s",Delimiter=',');
            preamble_list=preamble_list{1,1};
    
            fclose(raw_file);
            fclose(param_file);
    
            if numel(preamble_list) ~= 10
                error('Parameter list must contain 10 values.');
            end
            %parse the list
            format = str2double(preamble_list{1});
            type = str2double(preamble_list{2});
            points = str2double(preamble_list{3});
            count = str2double(preamble_list{4});
            xincrement = str2double(preamble_list{5});
            xorigin = str2double(preamble_list{6});
            xreference = str2double(preamble_list{7});
            yincrement = str2double(preamble_list{8});
            yorigin = str2double(preamble_list{9});
            yreference = str2double(preamble_list{10});
    
    
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
    Phase(CurrentIndex) = Uph_deg(2)-Uph_deg(1);
    end
    if USE_AS_COMPENSATION_CURVE == true
        disp("Using this measurement as compensation curve")
        Gain_compensation = Gain;
        Phase_compensation = Phase;
        Frequency_list_compensation = Frequency_list;
        save Compensation_curve Gain_compensation Phase_compensation Frequency_list_compensation;
    else
        disp("Printing phase and amplitude to .mat")
        save Bode_plot_data Gain Phase Frequency_list;
    end
end
    