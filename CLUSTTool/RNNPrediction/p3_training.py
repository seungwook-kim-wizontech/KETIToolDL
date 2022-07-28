import pandas as pd
import os, sys
sys.path.append("../")

# 
from KETIToolDL.CLUSTTool.common import p1_integratedDataSaving as p1

def getScaledData(scalerParam, scalerRootpath, data):
    if scalerParam=='scale':
        from KETIPreDataTransformation.general_transformation.dataScaler import DataScaler
        DS = DataScaler('minmax', scalerRootpath )
        #from KETIPreDataTransformation.general_transformation import dataScaler
        #feature_col_list = dataScaler.get_scalable_columns(train_o)
        DS.setScaleColumns(list(data.columns))
        DS.setNewScaler(data)
        resultData = DS.transform(data)
        scalerFilePath = DS.scalerFilePath
    else:
        resultData = data.copy()
        scalerFilePath=None

    return resultData, scalerFilePath


def getTrainValData(data, featureList, scalerRootPath, splitRatio, scalerParam):
    trainval, scalerFilePath = getScaledData(scalerParam, scalerRootPath, data[featureList])
    from KETIPreDataTransformation.trans_for_purpose import machineLearning as ML
    train, val = ML.splitDataByRatio(trainval, splitRatio)
    
    return train, val, scalerFilePath

def cleanNaNDF(dataSet, NaNProcessingParam, timedelta_frequency_sec):
    feature_cycle=NaNProcessingParam['feature_cycle']
    feature_cycle_times=NaNProcessingParam['feature_cycle_times']
    NanInfoForCleanData=NaNProcessingParam['NanInfoForCleanData']

    feature_list = dataSet.columns
    from KETIPreDataIngestion.dataByCondition import cycle_Module

    dayCycle = cycle_Module.getCycleSelectDataSet(dataSet, feature_cycle, feature_cycle_times, timedelta_frequency_sec)
    import matplotlib.pyplot as plt

    from KETIPreDataSelection.dataRemovebyNaN import clean_feature_data
    CMS = clean_feature_data.CleanFeatureData(feature_list, timedelta_frequency_sec)
    refinedData, filterImputedData = CMS.getMultipleCleanDataSetsByDF(dayCycle, NanInfoForCleanData)
    CleanData = pd.concat(filterImputedData.values())
    return CleanData

def trainSaveModel(trainModelMetaPath, train, val,  dataName, cleanTrainDataParam, NaNProcessingParam, transformParameter, scalerParam,  model_method,  trainParameter, batch_size, n_epochs, trainDataInfo, modelTags, trainDataType, modelPurpose, scalerFilePath):

    from KETIPreDataTransformation.general_transformation.dataScaler import encodeHashStyle
    transformParameter_encode =  encodeHashStyle(str(transformParameter))
    trainDataPathList = ["CLUST", dataName, transformParameter_encode]

    from KETIToolDL.TrainTool.trainer import RNNStyleModelTrainer as RModel
    RM= RModel()
    RM.processInputData(train, val, transformParameter, cleanTrainDataParam, batch_size)

    from KETIToolDL import modelInfo
    MI = modelInfo.ModelFileManager()
    modelFilePath = MI.getModelFilePath(trainDataPathList, model_method)

    RM.setTrainParameter(trainParameter)
    RM.getModel(model_method)
    RM.trainModel(n_epochs, modelFilePath)

    modelMeta = p1.readJsonData(trainModelMetaPath)
    modelName, modelInfoMeta = setModelData(dataName, modelMeta, trainDataInfo, modelTags, cleanTrainDataParam, NaNProcessingParam, transformParameter, scalerParam, trainParameter, transformParameter_encode, model_method, trainDataType, modelPurpose, scalerFilePath, modelFilePath)
    p1.writeJsonData(trainModelMetaPath, modelMeta)

    return modelName, modelFilePath, modelInfoMeta

def setModelData(dataName, modelMeta, trainDataInfo, modelTags, cleanTrainDataParam, NaNProcessingParam, transformParameter, scalerParam, trainParameter, transformParameter_encode, model_method, trainDataType, modelPurpose, scalerFilePath, modelFilePath):
    
    from KETIPreDataTransformation.general_transformation.dataScaler import encodeHashStyle
    ModelName = encodeHashStyle (p1.getListMerge ([transformParameter_encode, dataName] ))

    modelInfoMeta ={}
    modelInfoMeta ["trainDataInfo"] = trainDataInfo
    modelInfoMeta ["featureList"] = transformParameter["feature_col"]
    modelInfoMeta ["trainDataType"] = trainDataType
    modelInfoMeta ["modelPurpose"] = modelPurpose
    modelInfoMeta ["model_method"] = model_method
    modelInfoMeta ["modelTags"] = modelTags
    modelInfoMeta ["cleanTrainDataParam"] = cleanTrainDataParam
    modelInfoMeta ["NaNProcessingParam"] = NaNProcessingParam
    modelInfoMeta ["dataName"]=dataName
    modelInfoMeta ["transformParameter"]=transformParameter
    modelInfoMeta ["scalerParam"] =scalerParam
    modelInfoMeta ["scalerFilePath"] = scalerFilePath
    modelInfoMeta ["modelFilePath"] =modelFilePath
    modelInfoMeta ["trainParameter"] =trainParameter

    modelMeta[ModelName]=modelInfoMeta
    return ModelName, modelInfoMeta
