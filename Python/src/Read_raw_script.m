clc
clear

DirPath = "C:/Users/Arthur/Documents/Linas_B/Measurement_data/";
FileName = "RAW_CH1_2026_03_13_19_43_41.bin";

raw_file = fopen(DirPath+FileName);
%no preamble, read full data
raw_data = fread(raw_file,"uint16");
index = 0:1:length(raw_data)-1;
plot(index,raw_data)
