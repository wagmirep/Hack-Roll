import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  TouchableOpacity,
  Image,
  ScrollView,
} from 'react-native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RouteProp } from '@react-navigation/native';
import { RecordStackParamList } from '../navigation/MainNavigator';
import { LinearGradient } from 'expo-linear-gradient';

type WrappedScreenNavigationProp = StackNavigationProp<RecordStackParamList, 'Wrapped'>;
type WrappedScreenRouteProp = RouteProp<RecordStackParamList, 'Wrapped'>;

interface Props {
  navigation: WrappedScreenNavigationProp;
  route: WrappedScreenRouteProp;
}

interface WrappedData {
  singlishWordsCount: number;
  totalWords: number;
  sessionDuration: string;
  topWords?: Array<{ word: string; count: number }>;
}

export default function WrappedScreen({ navigation, route }: Props) {
  // Mock data - replace with actual data from route params or API
  const data: WrappedData = route.params?.data || {
    singlishWordsCount: 23,
    totalWords: 47,
    sessionDuration: '5:34',
    topWords: [
      { word: 'lah', count: 8 },
      { word: 'walao', count: 5 },
      { word: 'sia', count: 4 },
    ],
  };

  const handleClose = () => {
    navigation.goBack();
  };

  return (
    <LinearGradient
      colors={['#F29D9D', '#F5A8A8']}
      style={styles.container}
    >
      <SafeAreaView style={styles.safeArea}>
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Page indicators */}
          <View style={styles.pageIndicators}>
            <View style={[styles.indicator, styles.indicatorActive]} />
            <View style={styles.indicator} />
            <View style={styles.indicator} />
          </View>

          {/* Close button */}
          <TouchableOpacity
            style={styles.closeButton}
            onPress={handleClose}
          >
            <Text style={styles.closeIcon}>✕</Text>
          </TouchableOpacity>

          {/* Logo */}
          <View style={styles.logoContainer}>
            <View style={styles.logoCircle}>
              <Image
                source={require('../../assets/images/rabak-logo.jpg')}
                style={styles.logoImage}
                resizeMode="contain"
              />
            </View>
          </View>

          {/* Title */}
          <Text style={styles.title}>Your yap session wrapped</Text>

          {/* Main stat */}
          <View style={styles.mainStatContainer}>
            <Text style={styles.statLabel}>You said</Text>
            <Text style={styles.bigNumber}>{data.singlishWordsCount}</Text>
            <Text style={styles.statSubtitle}>Singlish words</Text>
          </View>

          {/* Additional stats */}
          <View style={styles.additionalStats}>
            <Text style={styles.additionalStatText}>
              That's {data.totalWords} words total
            </Text>
            <Text style={styles.additionalStatText}>
              Session lasted {data.sessionDuration}
            </Text>
          </View>

          {/* Top words preview (if available) */}
          {data.topWords && data.topWords.length > 0 && (
            <View style={styles.topWordsPreview}>
              <Text style={styles.topWordsLabel}>Top words:</Text>
              <View style={styles.topWordsList}>
                {data.topWords.map((item, index) => (
                  <View key={index} style={styles.topWordItem}>
                    <Text style={styles.topWord}>
                      {item.word} ({item.count})
                    </Text>
                  </View>
                ))}
              </View>
            </View>
          )}
        </ScrollView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 32,
    paddingTop: 20,
    paddingBottom: 40,
  },
  pageIndicators: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 20,
  },
  indicator: {
    width: 100,
    height: 4,
    backgroundColor: 'rgba(0, 0, 0, 0.2)',
    borderRadius: 2,
  },
  indicatorActive: {
    backgroundColor: '#000000',
  },
  closeButton: {
    position: 'absolute',
    top: 20,
    right: 32,
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
  },
  closeIcon: {
    fontSize: 28,
    color: '#000000',
    fontWeight: '300',
  },
  logoContainer: {
    alignItems: 'center',
    marginTop: 40,
    marginBottom: 30,
  },
  logoCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    borderWidth: 3,
    borderColor: '#000000',
    backgroundColor: '#ED4545',
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
  },
  logoImage: {
    width: '70%',
    height: '70%',
  },
  title: {
    fontSize: 32,
    fontWeight: '400',
    color: '#000000',
    textAlign: 'center',
    marginBottom: 60,
    letterSpacing: 0.3,
  },
  mainStatContainer: {
    alignItems: 'center',
    marginBottom: 50,
  },
  statLabel: {
    fontSize: 20,
    color: '#000000',
    marginBottom: 10,
    fontWeight: '400',
  },
  bigNumber: {
    fontSize: 120,
    fontWeight: '700',
    color: '#000000',
    lineHeight: 130,
    marginVertical: 10,
  },
  statSubtitle: {
    fontSize: 24,
    color: '#000000',
    fontWeight: '400',
    marginTop: 5,
  },
  additionalStats: {
    alignItems: 'center',
    gap: 8,
    marginBottom: 40,
  },
  additionalStatText: {
    fontSize: 16,
    color: 'rgba(0, 0, 0, 0.7)',
    fontWeight: '400',
  },
  topWordsPreview: {
    marginTop: 20,
    alignItems: 'center',
  },
  topWordsLabel: {
    fontSize: 18,
    color: '#000000',
    fontWeight: '500',
    marginBottom: 15,
  },
  topWordsList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 10,
  },
  topWordItem: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: 'rgba(0, 0, 0, 0.1)',
    borderRadius: 20,
  },
  topWord: {
    fontSize: 14,
    color: '#000000',
    fontWeight: '500',
  },
});
