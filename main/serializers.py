# serializers.py - ATUALIZADO COM CONVERSÃO UTC-4
from rest_framework import serializers
from .models import RegistroPonto, Funcionario
from django.utils import timezone
import pytz


class PontoHistoricoSerializer(serializers.ModelSerializer):
    funcionarioId = serializers.IntegerField(source='funcionario.user.id', read_only=True)
    funcionarioNome = serializers.CharField(source='funcionario.user.get_full_name', read_only=True)
    tipo = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()
    hora = serializers.SerializerMethodField()
    timestamp_local = serializers.SerializerMethodField()  # 🆕 NOVO CAMPO

    class Meta:
        model = RegistroPonto
        fields = ('id', 'funcionarioId', 'funcionarioNome', 'tipo', 'timestamp', 'timestamp_local', 'data', 'hora',
                  'observacao')

    def get_tipo(self, obj):
        return obj.get_tipo_display().lower()

    def converter_para_manaus(self, timestamp_utc):
        """
        Converte timestamp UTC para UTC-4 (Manaus)
        """
        try:
            utc_tz = pytz.UTC
            manaus_tz = pytz.timezone('America/Manaus')

            # Se já é timezone aware, converte diretamente
            if timezone.is_aware(timestamp_utc):
                return timestamp_utc.astimezone(manaus_tz)
            else:
                # Se é naive, assume UTC e converte
                timestamp_utc = utc_tz.localize(timestamp_utc)
                return timestamp_utc.astimezone(manaus_tz)
        except Exception:
            return timestamp_utc

    def get_timestamp_local(self, obj):
        """🆕 Retorna o timestamp convertido para UTC-4"""
        timestamp_local = self.converter_para_manaus(obj.timestamp)
        return timestamp_local.strftime('%d/%m/%Y %H:%M:%S')

    def get_data(self, obj):
        """🆕 Agora usa UTC-4"""
        timestamp_local = self.converter_para_manaus(obj.timestamp)
        return timestamp_local.strftime('%d/%m/%Y')

    def get_hora(self, obj):
        """🆕 Agora usa UTC-4"""
        timestamp_local = self.converter_para_manaus(obj.timestamp)
        return timestamp_local.strftime('%H:%M')


class FuncionarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Funcionario
        fields = ('id', 'user', 'cpf', 'telefone', 'endereco', 'cargo', 'data_admissao')